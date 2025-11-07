from __future__ import annotations

import os
import sys
import time
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

# ────────────────────────────────────────────────────────────
# 실행 옵션 (3회 테스트 유지)
# ────────────────────────────────────────────────────────────
DRY_RUN: bool = False           # 👈 DB에 실제 쓰기 (False)
LIMIT_PER_BRAND: int = 2        # 👈 브랜드당 2개만 가져옴 (테스트용)
SLEEP_SEC: float = 1.3
TEST_BRANDS: List[str] | None = [
    "Chanel"]

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
from app.services.catalog.fragella_service import (
    FragellaClient,
    TOP_BRANDS as _TOP_BRANDS,
    FragellaError,
)

def log(*args):
    print(*args, flush=True)

# ────────────────────────────────────────────────────────────
# 헬퍼 함수
# ────────────────────────────────────────────────────────────

def extract_and_clean(data: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    """Fragella 응답에서 필요한 필드를 추출하고 None이면 빈 값으로 클린업합니다."""
    result = {}
    for key in keys:
        value = data.get(key)
        # JSON/List 타입 필드가 None이면 빈 리스트/딕셔너리로 변환하여 DB 저장 오류 방지
        if key in ["General Notes", "Top Notes", "Middle Notes", "Base Notes", "Main Accords"]:
            result[key] = value or []
        elif key in ["Main Accords Percentage", "Season Ranking", "Occasion Ranking"]:
            result[key] = value or {}
        else:
            result[key] = value
    return result

def update_perfume_detail(db, perfume: Perfume, detail_data: Dict[str, Any]):
    """
    DB에 존재하는 Perfume 객체를 상세 API 응답 데이터로 업데이트합니다.
    (이 함수가 핵심적으로 상세 정보를 DB에 반영합니다.)
    """
    
    # 🚨 상세 정보 필드들을 매핑하여 업데이트
    update_data = extract_and_clean(detail_data, [
        "Price", "Longevity", "Sillage",
        "Gender", "Purchase URL", 
        "General Notes", "Top Notes", "Middle Notes", "Base Notes", 
        "Main Accords", "Main Accords Percentage", 
        "Season Ranking", "Occasion Ranking",
        "Currency", "Image Fallbacks"
    ])
    
    # Perfume 모델 필드 이름에 맞게 변환
    mapping = {
        "Price": "price", "Longevity": "longevity", "Sillage": "sillage",
        "Gender": "gender", "Purchase URL": "purchase_url",
        "General Notes": "general_notes", "Top Notes": "top_notes", 
        "Middle Notes": "middle_notes", "Base Notes": "base_notes", 
        "Main Accords": "main_accords", "Main Accords Percentage": "main_accords_percentage",
        "Season Ranking": "season_ranking", "Occasion Ranking": "occasion_ranking",
        "Currency": "currency", "Image Fallbacks": "image_fallbacks"
    }
    
    for fragella_key, model_key in mapping.items():
        if fragella_key in update_data:
            setattr(perfume, model_key, update_data[fragella_key])

    # 🚨 last_synced_at 업데이트 (시간 문제 해결)
    perfume.last_synced_at = datetime.now()


def upsert_brand_and_perfumes_summary(db, brand_name: str, summary_items: List[Dict[str, Any]]) -> tuple[Brand, list[Perfume]]:
    """
    브랜드와 향수 요약 정보(ID, Name)를 DB에 저장/업데이트합니다.
    Perfume 객체를 리스트로 반환하여 다음 단계(상세 조회)에 사용합니다.
    """
    perfume_objects = []
    
    # 1) 브랜드 upsert
    brand = db.query(Brand).filter(Brand.name == brand_name).first()
    if not brand:
        brand = Brand(name=brand_name)
        if not DRY_RUN:
            db.add(brand)
            db.flush() # id 확보

    # 2) 향수 요약 정보 upsert
    for it in summary_items:
        fragella_id = str(it.get("Fragella_ID") or it.get("ID"))
        name = it.get("Name")
        image_url = it.get("Image URL")
        gender = it.get("Gender")
        
        if not fragella_id or not name:
            continue

        perfume = db.query(Perfume).filter(Perfume.fragella_id == fragella_id).first()
        
        if not perfume:
            # 신규 insert
            perfume = Perfume(
                name=name,
                brand_id=brand.id,
                brand_name=brand_name,
                fragella_id=fragella_id,
                image_url=image_url,
                gender=gender,
            )
            if not DRY_RUN:
                db.add(perfume)
                db.flush() # id 확보
        else:
            # 기존 업데이트 (요약 정보만)
            if not DRY_RUN:
                perfume.name = name
                perfume.image_url = image_url
                perfume.gender = gender

        perfume_objects.append(perfume)
        
    if not DRY_RUN:
        db.commit() # 요약 정보 저장/업데이트 커밋
        
    return brand, perfume_objects


# ────────────────────────────────────────────────────────────
# 메인 동기화 함수 (수정)
# ────────────────────────────────────────────────────────────

def sync_top_brands():
    client = FragellaClient()
    
    brands_to_sync = TEST_BRANDS if TEST_BRANDS and TEST_BRANDS != [] else _TOP_BRANDS
    
    try:
        usage = client.get_usage()
        log("[Fragella usage BEFORE]", usage)
    except Exception:
        log("[Fragella] usage 조회 실패(무시)")

    log(f"[Sync] target brands = {len(brands_to_sync)}, limit_per_brand={LIMIT_PER_BRAND}")

    total_upserted_perfumes = 0
    total_synced_details = 0 # 상세 정보 업데이트 카운터 추가

    with SessionLocal() as db:
        for brand in brands_to_sync:
            try:
                log(f"  - syncing brand: {brand} (Phase 1: Summary List)...")
                
                # 1. 목록 API 호출 (1회 소모)
                summary_items = client.list_fragrances_by_brand(brand, limit=LIMIT_PER_BRAND)
                
                # 2. 요약 정보 DB에 저장/업데이트
                _, perfume_objects = upsert_brand_and_perfumes_summary(db, brand, summary_items)
                
                log(f"    -> Found {len(perfume_objects)} perfumes. (Phase 2: Detail Sync)")
                
                # 3. 개별 향수 상세 조회 및 업데이트 (N회 소모)
                for p_obj in perfume_objects:
                    fragella_id = p_obj.fragella_id
                    if not fragella_id:
                        log(f"    !! 경고: Perfume ID {p_obj.id.hex()[:8]}...에 Fragella ID 없음. 스킵.")
                        continue
                    
                    # 🚨 상세 API 호출 (1회 소모)
                    detail_data = client.get_fragrance_detail(fragella_id)
                    
                    # 🚨 상세 정보로 DB 업데이트 (핵심 로직)
                    update_perfume_detail(db, p_obj, detail_data)
                    
                    # 🚨 1.3초 슬립 (API 호출 간격 준수)
                    time.sleep(SLEEP_SEC) 
                    
                    total_synced_details += 1

                if not DRY_RUN:
                    db.commit() # 상세 정보 업데이트 커밋
                
                total_upserted_perfumes += len(perfume_objects)
                log(f"    -> DONE. Total {len(perfume_objects)} perfumes fully synced.")
                
            except FragellaError as e:
                log(f"    !! 실패 (Fragella): {e}")
            except Exception as e:
                log(f"    !! 예외: {type(e).__name__}: {e}")
            
            # 브랜드별 동기화 후 커밋 보장
            if not DRY_RUN:
                db.commit()


    log(f"[Sync DONE] Total Perfumes Upserted={total_upserted_perfumes}, Total Details Synced={total_synced_details}")

    try:
        usage = client.get_usage()
        log("[Fragella usage AFTER]", usage)
    except Exception:
        log("[Fragella] usage 조회 실패(무시)")


if __name__ == "__main__":
    sync_top_brands()