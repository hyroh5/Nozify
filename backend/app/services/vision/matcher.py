from typing import List, Dict, Any, Tuple
import json, os, re
from rapidfuzz import fuzz, process
from app.core.config import VisionConfig

# ---------- 로딩 & 전처리 ----------
def _load_json(path: str):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

_BRANDS = _load_json(VisionConfig.BRANDS_JSON)
_PRODUCTS = _load_json(VisionConfig.PRODUCTS_JSON)

# id -> brand dict
_BRAND_BY_ID = {b["id"]: b for b in _BRANDS}
# brand_id -> [product dicts]
_PRODUCTS_BY_BRAND = {}
for p in _PRODUCTS:
    _PRODUCTS_BY_BRAND.setdefault(p["brand_id"], []).append(p)

_STOPWORDS = {"EAU","DE","THE","OF"}  # 필요 시 확장
_CONC_KEYWORDS = {"EDT","EDP","INTENSE"}

def normalize_text(s: str) -> str:
    s = s.upper()
    s = s.replace("’","'").replace("‘","'").replace("`","'")
    s = re.sub(r"[^\w\s]", " ", s)   # 특수문자 제거
    s = re.sub(r"\s+", " ", s).strip()
    return s

def tokenize(s: str) -> List[str]:
    toks = normalize_text(s).split()
    out=[]
    for t in toks:
        if len(t) < 2 and t not in _CONC_KEYWORDS:
            continue
        if t in _STOPWORDS:
            continue
        out.append(t)
    return out

# ---------- 점수 계산 ----------
def _max_alias_score(aliases: List[str], text_tokens: List[str]) -> float:
    # alias 하나라도 텍스트 토큰들과 부분 일치하면 가산
    best = 0.0
    joined = " ".join(text_tokens)
    for a in aliases:
        a_norm = normalize_text(a)
        # 부분 문자열 유사도(편집거리) 기반
        score = fuzz.partial_ratio(a_norm, joined) / 100.0
        if score > best:
            best = score
    return best

def match_brand(text_tokens: List[str]) -> List[Tuple[Dict[str,Any], float]]:
    candidates=[]
    for b in _BRANDS:
        score = _max_alias_score(b.get("aliases",[b["name"]]), text_tokens)
        if score > 0:
            candidates.append((b, score))
    candidates.sort(key=lambda x: (-x[1], x[0]["name"]))
    return candidates[:3]

def match_product(brand_id: str, text_tokens: List[str], user_query_tokens: List[str]) -> List[Tuple[Dict[str,Any], float]]:
    items = _PRODUCTS_BY_BRAND.get(brand_id, [])
    joined = " ".join(text_tokens)
    jq = " ".join(user_query_tokens) if user_query_tokens else ""
    results=[]
    for p in items:
        alias_list = p.get("aliases",[p["name"]])
        base = 0.0
        # 기본: OCR 토큰과의 부분일치
        for a in alias_list:
            a_norm = normalize_text(a)
            base = max(base, fuzz.partial_ratio(a_norm, joined)/100.0)
        # 사용자 입력 가중치
        if jq:
            for a in alias_list:
                a_norm = normalize_text(a)
                base = max(base, 0.9*base + 0.1*(fuzz.partial_ratio(a_norm, jq)/100.0))
        # 농도 키워드 보너스
        for k in _CONC_KEYWORDS:
            if k in text_tokens and k in tokenize(p["name"]):
                base += 0.05
        results.append((p, min(base, 1.0)))
    results.sort(key=lambda x: (-x[1], x[0]["name"]))
    return results[:3]

def get_match(texts: List[Dict[str,Any]], user_query: str="") -> Dict[str,Any]:
    # OCR 토큰 합치기
    ocr_tokens=[]
    for t in texts:
        ocr_tokens.extend(tokenize(t.get("text","")))
    if not ocr_tokens:
        return {"final": None, "candidates": []}

    brand_cands = match_brand(ocr_tokens)
    if not brand_cands or brand_cands[0][1] < 0.7:  # 브랜드 임계 예시
        return {"final": None, "candidates": []}

    user_tokens = tokenize(user_query) if user_query else []
    # 상위 브랜드 1~2개까지 제품 후보 뽑고, 스코어 상위만 합치기
    prod_candidates = []
    for b, bscore in brand_cands[:2]:
        prods = match_product(b["id"], ocr_tokens, user_tokens)
        for p, pscore in prods:
            final_score = 0.3*bscore + 0.6*pscore + 0.1*(1.0 if user_tokens else 0.0)
            prod_candidates.append({
                "brand": b["name"], "product": p["name"], "product_id": p["id"], "score": round(min(final_score,1.0), 3)
            })

    prod_candidates.sort(key=lambda x: (-x["score"], x["product"]))
    final = prod_candidates[0] if (prod_candidates and prod_candidates[0]["score"] >= VisionConfig.THRESH_TEXT_MATCH) else None

    return {
        "final": final,
        "candidates": prod_candidates[:3]
    }
