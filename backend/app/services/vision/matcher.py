# backend/app/services/vision/matcher.py

from typing import List, Dict, Any, Tuple
import re
from functools import lru_cache

from rapidfuzz import fuzz
from app.core.config import VisionConfig

from app.core.db import SessionLocal
from app.models.brand import Brand
from app.models.perfume import Perfume


# ---------- DB 로딩 ----------

@lru_cache(maxsize=1)
def _load_from_db() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    brand, perfume 전체를 DB에서 읽어서
    매칭에 쓰기 좋은 dict 리스트 형태로 변환한다.
    - id / brand_id 는 BINARY(16) → hex 문자열로 변환해서 사용
    """
    db = SessionLocal()
    try:
        brands: List[Brand] = db.query(Brand).all()
        perfumes: List[Perfume] = db.query(Perfume).all()

        brand_dicts: List[Dict[str, Any]] = []
        product_dicts: List[Dict[str, Any]] = []

        for b in brands:
            # BINARY(16) → hex string
            bid = b.id.hex() if isinstance(b.id, (bytes, bytearray)) else str(b.id)
            name = b.name or ""

            brand_dicts.append(
                {
                    "id": bid,
                    "name": name,
                    # 나중에 다른 별칭 컬럼이 생기면 여기에 추가
                    "aliases": [name],
                }
            )

        for p in perfumes:
            pid = p.id.hex() if isinstance(p.id, (bytes, bytearray)) else str(p.id)
            bid = p.brand_id.hex() if isinstance(p.brand_id, (bytes, bytearray)) else str(p.brand_id)
            name = p.name or ""

            aliases = [name]
            if getattr(p, "brand_name", None):
                aliases.append(p.brand_name)
            if getattr(p, "concentration", None):
                aliases.append(p.concentration)

            # 1) 이미지 URL 가져오기 (컬럼명이 다르면 여기만 바꾸면 됨)
            image_url = getattr(p, "image_url", None)

            product_dicts.append(
                {
                    "id": pid,
                    "brand_id": bid,
                    "name": name,
                    "aliases": aliases,
                    "image_url": image_url,   # ← 추가
                }
            )


        print(f"[LOG][MATCH][INIT] loaded brands={len(brand_dicts)}, perfumes={len(product_dicts)}")
        return brand_dicts, product_dicts
    except Exception as e:
        print("[LOG][MATCH][INIT][ERROR] DB load failed:", e)
        return [], []
    finally:
        db.close()


# 전역 캐시 (기존 JSON 기반 구조와 동일한 인터페이스 유지)
_BRANDS, _PRODUCTS = _load_from_db()

# id -> brand dict
_BRAND_BY_ID: Dict[str, Dict[str, Any]] = {b["id"]: b for b in _BRANDS}

# brand_id -> [product dicts]
_PRODUCTS_BY_BRAND: Dict[str, List[Dict[str, Any]]] = {}
for p in _PRODUCTS:
    _PRODUCTS_BY_BRAND.setdefault(p["brand_id"], []).append(p)


# ---------- 전처리 ----------

_STOPWORDS = {"EAU", "DE", "THE", "OF"}  # 필요 시 확장
_CONC_KEYWORDS = {"EDT", "EDP", "INTENSE"}


def normalize_text(s: str) -> str:
    s = s.upper()
    s = s.replace("’", "'").replace("‘", "'").replace("`", "'")
    s = re.sub(r"[^\w\s]", " ", s)  # 특수문자 제거
    s = re.sub(r"\s+", " ", s).strip()
    return s


def tokenize(s: str) -> List[str]:
    toks = normalize_text(s).split()
    out: List[str] = []
    for t in toks:
        # 1글자 토큰은 농도 키워드가 아니면 무시
        if len(t) == 1 and t not in _CONC_KEYWORDS:
            continue
        # 2글자 토큰도 기본적으로 무시 (필요하면 화이트리스트 추가)
        if len(t) == 2 and t not in _CONC_KEYWORDS:
            # 예외적으로 살리고 싶은 약어가 있으면 여기서 허용
            # if t in {"CK", ...}: pass
            continue
        if t in _STOPWORDS:
            continue
        out.append(t)
    return out


# ---------- 점수 계산 ----------

def _max_alias_score(aliases: List[str], text_tokens: List[str]) -> float:
    """
    alias 리스트와 OCR 토큰들의 유사도 중 최대값을 반환
    RapidFuzz partial_ratio 기반, [0.0, 1.0] 범위
    """
    best = 0.0
    joined = " ".join(text_tokens)
    for a in aliases:
        a_norm = normalize_text(a)
        score = fuzz.partial_ratio(a_norm, joined) / 100.0
        if score > best:
            best = score
    return best


def match_brand(text_tokens: List[str]) -> List[Tuple[Dict[str, Any], float]]:
    candidates: List[Tuple[Dict[str, Any], float]] = []
    for b in _BRANDS:
        score = _max_alias_score(b.get("aliases", [b["name"]]), text_tokens)
        if score > 0:
            candidates.append((b, score))
    candidates.sort(key=lambda x: (-x[1], x[0]["name"]))
    return candidates[:3]


def match_product(
    brand_id: str,
    text_tokens: List[str],
    user_query_tokens: List[str],
) -> List[Tuple[Dict[str, Any], float]]:
    items = _PRODUCTS_BY_BRAND.get(brand_id, [])
    joined = " ".join(text_tokens)
    jq = " ".join(user_query_tokens) if user_query_tokens else ""
    results: List[Tuple[Dict[str, Any], float]] = []

    for p in items:
        alias_list = p.get("aliases", [p["name"]])
        base = 0.0

        # 기본: OCR 토큰과의 부분 일치
        for a in alias_list:
            a_norm = normalize_text(a)
            base = max(base, fuzz.partial_ratio(a_norm, joined) / 100.0)

        # 사용자 입력 가중치
        if jq:
            for a in alias_list:
                a_norm = normalize_text(a)
                uq_score = fuzz.partial_ratio(a_norm, jq) / 100.0
                base = max(base, 0.9 * base + 0.1 * uq_score)

        # 농도 키워드 보너스
        name_tokens = tokenize(p["name"])
        for k in _CONC_KEYWORDS:
            if k in text_tokens and k in name_tokens:
                base += 0.05

        results.append((p, min(base, 1.0)))

    results.sort(key=lambda x: (-x[1], x[0]["name"]))
    return results[:3]


# ---------- 엔트리 포인트 ----------

def get_match(texts: List[Dict[str, Any]], user_query: str = "") -> Dict[str, Any]:
    """
    OCR 결과(texts)와 optional user_query를 받아
    - 브랜드 후보 점수
    - 각 브랜드별 향수 후보 점수
    를 계산하고,
    score 내림차순으로 정렬된 상위 후보와 최종 선택 1개를 반환한다.
    """
    print(f"[LOG][MATCH] 입력 텍스트={texts}, user_query={user_query}")

    # OCR 토큰 합치기
    ocr_tokens: List[str] = []
    for t in texts:
        ocr_tokens.extend(tokenize(t.get("text", "")))

    if not ocr_tokens:
        print("[LOG][MATCH] no OCR tokens")
        return {"final": None, "candidates": []}

    # 1) 브랜드 후보
    brand_cands = match_brand(ocr_tokens)
    if not brand_cands or brand_cands[0][1] < 0.7:
        # 브랜드가 전혀 안 맞으면 아직은 매칭 실패로 처리
        # 필요하면 여기서 '브랜드 무시하고 전체 향수에서 매칭' fallback 추가 가능
        print("[LOG][MATCH] no reliable brand candidate")
        return {"final": None, "candidates": []}

    user_tokens = tokenize(user_query) if user_query else []

    # 2) 상위 브랜드 1~2개에서 제품 후보 뽑기
    prod_candidates: List[Dict[str, Any]] = []
    for b, bscore in brand_cands[:2]:
        prods = match_product(b["id"], ocr_tokens, user_tokens)
        for p, pscore in prods:
            final_score = 0.3 * bscore + 0.6 * pscore + 0.1 * (1.0 if user_tokens else 0.0)

            prod_candidates.append(
                {
                    "brand": b["name"],
                    "brand_id": b["id"],
                    "product": p["name"],
                    "product_id": p["id"],
                    "score": round(min(final_score, 1.0), 3),
                    # 2) 여기서 image_url을 그대로 흘려보냄
                    "image_url": p.get("image_url"),
                }
            )


    prod_candidates.sort(key=lambda x: (-x["score"], x["product"]))
    final = (
        prod_candidates[0]
        if (prod_candidates and prod_candidates[0]["score"] >= VisionConfig.THRESH_TEXT_MATCH)
        else None
    )

    print(f"[LOG][MATCH] 최종 매칭 결과={final}, 후보군={prod_candidates[:3]}")

    return {
        "final": final,
        "candidates": prod_candidates[:3],
    }
