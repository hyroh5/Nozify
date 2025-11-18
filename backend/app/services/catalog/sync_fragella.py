# backend/app/services/catalog/sync_fragella.py
from __future__ import annotations

import os
import sys
import time
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Tuple

# ────────────────────────────────────────────────────────────
# 실행 옵션
# ────────────────────────────────────────────────────────────
DRY_RUN: bool = False          # 실제 DB write 여부
LIMIT_PER_BRAND: int = 30       # 브랜드당 최대 가져올 개수
SLEEP_SEC: float = 0.6         # 호출 사이 딜레이(429 완화)
TEST_BRANDS: List[str] | None = [
 "Chanel","Dior","Yves Saint Laurent","Gucci","Versace","Giorgio Armani",
 "Tom Ford","Hermes","Maison Francis Kurkdjian","Jo Malone London","Byredo",
 "Diptyque","Montblanc","Mugler","Calvin Klein","Burberry","Givenchy","Guerlain",
]  # 테스트 시 소량만

# ────────────────────────────────────────────────────────────
# sys.path / .env 로드
# ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # .../Nozify
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=False)

# ────────────────────────────────────────────────────────────
# 앱 import
# ────────────────────────────────────────────────────────────
from app.core.db import SessionLocal
from app.models import Brand, Perfume
from app.services.catalog.fragella_service import FragellaClient, FragellaError


def log(*args):
    print(*args, flush=True)


# ────────────────────────────────────────────────────────────
# 매핑 헬퍼
# ────────────────────────────────────────────────────────────
def _to_decimal_or_none(v: Any) -> Decimal | None:
    if v is None or v == "":
        return None
    try:
        return Decimal(str(v))
    except InvalidOperation:
        return None

def _ensure_list(v: Any) -> list:
    return v if isinstance(v, list) else []

def _ensure_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}

def map_fragella_item(it: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fragella 문서 기준 필드 매핑:
    - 키는 대소문자/공백 포함. 정확히 그대로 접근
    - Longevity / Sillage 는 설명어(Moderate 등) → 우리 스키마가 DECIMAL이면 None 저장
    - Notes 객체는 Top/Middle/Base 로 분해
    """
    name        = it.get("Name") or ""
    brand_name  = it.get("Brand") or ""
    image_url   = it.get("Image URL") or ""
    gender      = it.get("Gender") or ""  # women / men / unisex 등
    price_dec   = _to_decimal_or_none(it.get("Price"))  # 문자열 가격을 Decimal 로 변환 시도
    currency    = it.get("Currency") or None

    # 설명어라 수치 저장 곤란 → DECIMAL 컬럼이면 None 유지, 문자열 컬럼이면 그대로 사용
    longevity   = it.get("Longevity") or None
    sillage     = it.get("Sillage") or None

    main_acc    = _ensure_list(it.get("Main Accords"))
    main_acc_pct= _ensure_dict(it.get("Main Accords Percentage"))
    season_rank = _ensure_list(it.get("Season Ranking"))
    occasion_rk = _ensure_list(it.get("Occasion Ranking"))
    image_falls = _ensure_list(it.get("Image Fallbacks"))
    purchase_url= it.get("Purchase URL") or None

    # Notes → Top/Middle/Base 분리
    notes_obj   = _ensure_dict(it.get("Notes"))
    top_notes   = _ensure_list(notes_obj.get("Top"))
    middle_notes= _ensure_list(notes_obj.get("Middle"))
    base_notes  = _ensure_list(notes_obj.get("Base"))

    # Fragella 문서는 별도의 ID 를 제공하지 않음 → 외부 식별자는 Name+Brand 조합으로 고정
    external_source = "fragella"
    external_id = f"{brand_name}||{name}".strip()

    return {
        "name": name,
        "brand_name": brand_name,
        "image_url": image_url,
        "gender": gender,
        "price": price_dec,
        "currency": currency,
        "longevity": longevity,     # 우리 스키마가 DECIMAL 이면 None 로 남음
        "sillage": sillage,         # 우리 스키마가 DECIMAL 이면 None 로 남음
        "main_accords": main_acc,
        "main_accords_percentage": main_acc_pct,
        "season_ranking": season_rank,
        "occasion_ranking": occasion_rk,
        "image_fallbacks": image_falls,
        "purchase_url": purchase_url,
        "top_notes": top_notes,
        "middle_notes": middle_notes,
        "base_notes": base_notes,
        "external_source": external_source,
        "external_id": external_id,
    }


def upsert_one(db, brand: Brand, mapped: Dict[str, Any]) -> Tuple[bool, bool]:
    """
    반환: (created, updated)
    - 외부 키는 (external_source, external_id) 로 고정
    """
    from sqlalchemy import and_
    created = updated = False

    # 먼저 기존 존재 확인
    p = (
        db.query(Perfume)
          .filter(
              Perfume.external_source == mapped["external_source"],
              Perfume.external_id == mapped["external_id"],
          )
          .first()
    )

    if p is None:
        # 신규 Insert
        p = Perfume(
            name=mapped["name"],
            brand_id=brand.id,
            brand_name=brand.name,
            image_url=mapped["image_url"],
            gender=mapped["gender"],
            price=mapped["price"],
            currency=mapped["currency"],
            longevity=None,  # 설명어 → 스키마가 DECIMAL 이므로 None
            sillage=None,    # 설명어 → 스키마가 DECIMAL 이므로 None
            main_accords=mapped["main_accords"],
            main_accords_percentage=mapped["main_accords_percentage"],
            top_notes=mapped["top_notes"],
            middle_notes=mapped["middle_notes"],
            base_notes=mapped["base_notes"],
            general_notes=None,  # 문서에 General Notes 배열도 있으나 Notes 와 중복 우려 → 필요 시 추가
            season_ranking=mapped["season_ranking"],
            occasion_ranking=mapped["occasion_ranking"],
            image_fallbacks=mapped["image_fallbacks"],
            purchase_url=mapped["purchase_url"],
            external_source=mapped["external_source"],
            external_id=mapped["external_id"],
        )
        if not DRY_RUN:
            db.add(p)
        created = True
    else:
        # 업데이트(핵심 필드만 덮어쓰기)
        if not DRY_RUN:
            p.name = mapped["name"] or p.name
            p.brand_id = brand.id
            p.brand_name = brand.name
            p.image_url = mapped["image_url"] or p.image_url
            p.gender = mapped["gender"] or p.gender
            p.price = mapped["price"] if mapped["price"] is not None else p.price
            p.currency = mapped["currency"] or p.currency

            # longevity/sillage(설명어)는 현 스키마 상 DECIMAL 이므로 저장 생략
            p.main_accords = mapped["main_accords"] or p.main_accords
            p.main_accords_percentage = mapped["main_accords_percentage"] or p.main_accords_percentage
            p.top_notes = mapped["top_notes"] or p.top_notes
            p.middle_notes = mapped["middle_notes"] or p.middle_notes
            p.base_notes = mapped["base_notes"] or p.base_notes
            p.season_ranking = mapped["season_ranking"] or p.season_ranking
            p.occasion_ranking = mapped["occasion_ranking"] or p.occasion_ranking
            p.image_fallbacks = mapped["image_fallbacks"] or p.image_fallbacks
            p.purchase_url = mapped["purchase_url"] or p.purchase_url
        updated = True

    return created, updated


def sync_top_brands():
    client = FragellaClient()

    # 사용량 조회(가능하면)
    try:
        usage = client.get_usage()
        log("[Fragella usage BEFORE]", usage)
    except Exception:
        log("[Fragella] usage 조회 실패(무시)")

    brands_to_sync = TEST_BRANDS or ["Dior", "Chanel"]

    log(f"[Sync] target brands = {len(brands_to_sync)}, limit_per_brand={LIMIT_PER_BRAND}")

    total_created = 0
    total_updated = 0

    with SessionLocal() as db:
        for brand_name in brands_to_sync:
            try:
                log(f"  - syncing brand: {brand_name} ...")
                arr = client.list_fragrances_by_brand(brand_name, limit=LIMIT_PER_BRAND)
                log(f"    -> fetched {len(arr)} items")

                # 1) 브랜드 upsert
                brand = db.query(Brand).filter(Brand.name == brand_name).first()
                if not brand:
                    brand = Brand(name=brand_name)
                    if not DRY_RUN:
                        db.add(brand)
                        db.flush()

                # 2) 향수 upsert
                created_cnt = 0
                updated_cnt = 0
                for it in arr:
                    mapped = map_fragella_item(it)
                    if not mapped["name"] or not mapped["brand_name"]:
                        continue

                    c, u = upsert_one(db, brand, mapped)
                    created_cnt += 1 if c else 0
                    updated_cnt += 1 if (u and not c) else 0

                    time.sleep(SLEEP_SEC)

                if not DRY_RUN:
                    db.commit()

                total_created += created_cnt
                total_updated += updated_cnt
                log(f"    -> upserted: created={created_cnt}, updated={updated_cnt}")

            except FragellaError as e:
                log(f"    !! 실패 (Fragella): {e}")
            except Exception as e:
                log(f"    !! 예외: {type(e).__name__}: {e}")

    log(f"[Sync DONE] created={total_created}, updated={total_updated}")

    # 사용량 재확인(가능하면)
    try:
        usage = client.get_usage()
        log("[Fragella usage AFTER]", usage)
    except Exception:
        log("[Fragella] usage 조회 실패(무시)")


if __name__ == "__main__":
    sync_top_brands()
