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

            if getattr(p, "concentration", None):
                aliases.append(p.concentration)

            image_url = getattr(p, "image_url", None)

            product_dicts.append(
                {
                    "id": pid,
                    "brand_id": bid,
                    "name": name,
                    "aliases": aliases,
                    "image_url": image_url,
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

        # OCR 토큰과의 부분 일치
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


def match_product_any_brand(
    text_tokens: List[str],
    user_query_tokens: List[str],
) -> List[Tuple[Dict[str, Any], float]]:
    """
    브랜드를 모를 때 전체 향수(_PRODUCTS)에서 바로 매칭하는 fallback.
    """
    joined = " ".join(text_tokens)
    jq = " ".join(user_query_tokens) if user_query_tokens else ""
    results: List[Tuple[Dict[str, Any], float]] = []

    for p in _PRODUCTS:
        alias_list = p.get("aliases", [p["name"]])
        base = 0.0

        for a in alias_list:
            a_norm = normalize_text(a)
            base = max(base, fuzz.partial_ratio(a_norm, joined) / 100.0)

        if jq:
            for a in alias_list:
                a_norm = normalize_text(a)
                uq_score = fuzz.partial_ratio(a_norm, jq) / 100.0
                base = max(base, 0.9 * base + 0.1 * uq_score)

        name_tokens = tokenize(p["name"])
        for k in _CONC_KEYWORDS:
            if k in text_tokens and k in name_tokens:
                base += 0.05

        results.append((p, min(base, 1.0)))

    results.sort(key=lambda x: (-x[1], x[0]["name"]))
    return results[:10]  # 전체 중 상위 10개까지만


def dedup_candidates(cands):
    seen = set()
    result = []
    for c in cands:
        pid = c["product_id"]
        if pid not in seen:
            seen.add(pid)
            result.append(c)
    return result


# ---------- 엔트리 포인트 ----------

def get_match(texts: List[Dict[str, Any]], user_query: str = "") -> Dict[str, Any]:
    print(f"[LOG][MATCH] 입력 텍스트={texts}, user_query={user_query}")

    # OCR 토큰 합치기
    ocr_tokens: List[str] = []
    for t in texts:
        ocr_tokens.extend(tokenize(t.get("text", "")))

    if not ocr_tokens:
        print("[LOG][MATCH] no OCR tokens")
        return {"final": None, "candidates": []}

    user_tokens = tokenize(user_query) if user_query else []

    # 1) 브랜드 후보
    brand_cands = match_brand(ocr_tokens)
    prod_candidates: List[Dict[str, Any]] = []

    # 브랜드가 충분히 신뢰할 만하면 기존 로직
    if brand_cands and brand_cands[0][1] >= 0.7:
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
                        "image_url": p.get("image_url"),
                    }
                )
    else:
        # 2) 브랜드가 안 잡히면 → 전체 향수에서 fallback 매칭
        print("[LOG][MATCH] no reliable brand → product-only fallback")
        prods = match_product_any_brand(ocr_tokens, user_tokens)
        for p, pscore in prods:
            bid = p["brand_id"]
            b = _BRAND_BY_ID.get(bid)
            bname = b["name"] if b else ""
            prod_candidates.append(
                {
                    "brand": bname,
                    "brand_id": bid,
                    "product": p["name"],
                    "product_id": p["id"],
                    "score": round(pscore, 3),
                    "image_url": p.get("image_url"),
                }
            )

    # 정렬 + 중복 제거
    prod_candidates.sort(key=lambda x: (-x["score"], x["product"]))
    prod_candidates = dedup_candidates(prod_candidates)
    top_candidates = prod_candidates[:3]

    final = (
        top_candidates[0]
        if (top_candidates and top_candidates[0]["score"] >= VisionConfig.THRESH_TEXT_MATCH)
        else None
    )

    print(f"[LOG][MATCH] 최종 매칭 결과={final}, 후보군={top_candidates}")

    return {
        "final": final,
        "candidates": top_candidates,
    }
