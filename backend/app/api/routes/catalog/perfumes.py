from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.core.db import get_db
from app.models.perfume import Perfume
from app.models.base import uuid_bytes_to_hex, uuid_hex_to_bytes, try_uuid_hex_to_bytes
from app.models.recent_view import RecentView
from app.api.deps import get_current_user_id
from uuid import uuid4, UUID
from app.models.user import User
from datetime import datetime

router = APIRouter(prefix="/catalog", tags=["Catalog"])

def _serialize_perfume(p: Perfume):
    return {
        "id": uuid_bytes_to_hex(p.id),
        "name": p.name,
        "brand_id": uuid_bytes_to_hex(p.brand_id),
        "brand_name": p.brand_name,
        "image_url": p.image_url,
        "gender": p.gender,
        "price": float(p.price) if p.price is not None else None,
        "currency": p.currency,
        "longevity": float(p.longevity) if p.longevity is not None else None,
        "sillage": float(p.sillage) if p.sillage is not None else None,
        "main_accords": p.main_accords,
        "main_accords_percentage": p.main_accords_percentage,
        "top_notes": p.top_notes,
        "middle_notes": p.middle_notes,
        "base_notes": p.base_notes,
        "general_notes": p.general_notes,
        "season_ranking": p.season_ranking,
        "occasion_ranking": p.occasion_ranking,
        "purchase_url": p.purchase_url,
        "fragella_id": p.fragella_id,
        "view_count": p.view_count,
        "wish_count": p.wish_count,
        "purchase_count": p.purchase_count,
    }

@router.get("/perfumes/{perfume_id}")
def get_perfume(
    perfume_id: str = Path(..., description="hex UUID 또는 fragella_id"),
    track_view: bool = Query(True, description="상세 조회 시 view_count 증가"),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_id),
):
    rid = uuid4().hex[:8]
    print(f"[VIEW][{rid}] track_view={track_view} id={perfume_id}")

    # User 객체에서 user_id bytes를 안전하게 추출
    user_id_bytes = None
    if current_user is not None:
        if hasattr(current_user, 'id'):
            user_id_bytes = current_user.id
        elif isinstance(current_user, bytes):
            user_id_bytes = current_user
        
    # 1) hex UUID 시도
    pk = try_uuid_hex_to_bytes(perfume_id)
    p = None
    if pk:
        p = db.get(Perfume, pk)

    # 2) 실패하면 fragella_id로도 조회 시도
    if p is None:
        p = db.query(Perfume).filter(Perfume.fragella_id == perfume_id).first()

    if not p:
        if pk is None and "-" not in perfume_id and len(perfume_id) not in (16, 32):
            raise HTTPException(status_code=400, detail="invalid id format: hex uuid 또는 fragella_id 사용")
        raise HTTPException(status_code=404, detail="perfume not found")
        
    if track_view:
        p.view_count = int(p.view_count or 0) + 1
        
        # 최근 본 항목 기록(유저 있을 때만) - UPSERT 로직
        if user_id_bytes:
            # 1. 기존 레코드가 있는지 확인 (User ID와 Perfume ID 기준)
            existing_view = (
                db.query(RecentView)
                .filter(RecentView.user_id == user_id_bytes, RecentView.perfume_id == p.id)
                .first()
            )

            if existing_view:
                # 2. 레코드가 있으면 viewed_at만 업데이트 (UPDATE)
                # 이 레코드를 최근 본 항목 리스트의 맨 위로 올립니다.
                existing_view.viewed_at = datetime.now()
                # 변경된 객체는 session에 이미 존재하므로 별도 db.add() 필요 없음
            else:
                # 3. 레코드가 없으면 새로 추가 (INSERT)
                db.add(RecentView(user_id=user_id_bytes, perfume_id=p.id))

        # View Count와 Recent View 변경사항을 동시에 커밋
        db.commit()
        db.refresh(p)

    return _serialize_perfume(p)

@router.get("/perfumes")
def list_perfumes(
# ... (rest of the file remains the same) ...
    brand_id: str | None = Query(None, description="hex 형식 UUID"),
    gender: str | None = Query(None, description="men / women / unisex"),
    q: str | None = Query(None, min_length=2, description="이름/브랜드 검색"),
    sort: str | None = Query(None, description="popular|recent"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User | None = Depends(get_current_user_id), # 비로그인 사용자도 호출 가능
    db: Session = Depends(get_db),
):
    query = db.query(Perfume)
    if brand_id:
        query = query.filter(Perfume.brand_id == uuid_hex_to_bytes(brand_id))
    if gender:
        query = query.filter(Perfume.gender == gender)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Perfume.name.ilike(like), Perfume.brand_name.ilike(like)))

    # 정렬
    if sort == "popular":
        query = query.order_by(Perfume.view_count.desc(), Perfume.wish_count.desc(), Perfume.id.desc())
    else:
        query = query.order_by(Perfume.created_at.desc(), Perfume.id.desc())

    items = query.offset(offset).limit(limit).all()
    return [
        {
            "id": uuid_bytes_to_hex(p.id),
            "name": p.name,
            "brand_name": p.brand_name,
            "image_url": p.image_url,
            "gender": p.gender,
            "view_count": p.view_count,
            "wish_count": p.wish_count,
        }
        for p in items
    ]

# ─────────────────────────────────────────
# 유사 향수 추천 (간단한 교집합 기반)
# ─────────────────────────────────────────
def _jaccard(a: list | None, b: list | None) -> float:
    A = set(a or [])
    B = set(b or [])
    if not A and not B:
        return 0.0
    return len(A & B) / max(1, len(A | B))

def _extract_note_names(notes: list | None) -> list[str]:
    if not notes:
        return []
    # notes는 [{"name": "...", "imageUrl": "..."}, ...] 형태이므로 'name' 키 값만 추출
    return [n.get("name") for n in notes if isinstance(n, dict) and n.get("name")]

@router.get("/perfumes/{perfume_id}/similar")
def similar_perfumes(
    perfume_id: str = Path(..., description="기준 향수 hex UUID"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    base = db.get(Perfume, uuid_hex_to_bytes(perfume_id))
    if not base:
        raise HTTPException(404, "base perfume not found")

    # 후보군: 같은 성별 우선, 최근/인기순 섞어서 상위 300개 정도에서 계산
    candidates = (
        db.query(Perfume)
          .filter(Perfume.id != base.id)
          .filter(Perfume.gender == base.gender if base.gender else True)
          .order_by(Perfume.view_count.desc(), Perfume.created_at.desc())
          .limit(300)
          .all()
    )

    base_acc = base.main_accords or []
    base_top = _extract_note_names(base.top_notes)
    base_mid = _extract_note_names(base.middle_notes)
    base_base = _extract_note_names(base.base_notes)
    base_any = (base.general_notes or []) + base_top + base_mid + base_base

    scored = []
    for p in candidates:
        p_top = _extract_note_names(p.top_notes)
        p_any_notes = _extract_note_names(p.top_notes) + _extract_note_names(p.middle_notes) + _extract_note_names(p.base_notes)

        s_acc = _jaccard(base_acc, p.main_accords)
        s_top = _jaccard(base_top, p_top)
        s_any = _jaccard(base_any, (p.general_notes or []) + p_any_notes)
        score = 0.6 * s_acc + 0.2 * s_top + 0.2 * s_any
        if score <= 0:
            continue
        scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for score, p in scored[:limit]:
        item = _serialize_perfume(p)
        item["similarity"] = round(float(score), 4)
        out.append(item)
    return {
        "base_id": uuid_bytes_to_hex(base.id),
        "base_name": base.name,
        "results": out,
    }

@router.get("/perfumes/popular")
def popular_perfumes(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    items = (
        db.query(Perfume)
          .order_by(Perfume.view_count.desc(), Perfume.wish_count.desc(), Perfume.id.desc())
          .offset(offset)
          .limit(limit)
          .all()
    )
    return [_serialize_perfume(p) for p in items]

@router.get("/perfumes/search")
def search_perfumes(
    q: str | None = Query(None, min_length=2, description="이름/브랜드 검색"),
    brand_id: str | None = Query(None, description="hex 형식 UUID"),
    gender: str | None = Query(None, description="men / women / unisex"),
    accords: str | None = Query(None, description="콤마구분 예: sweet,woody,citrus"),
    notes: str | None = Query(None, description="콤마구분 예: Bergamot,Jasmine"),
    sort: str | None = Query("relevance", description="relevance|popular|recent"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_total: bool = Query(False, description="총 개수 count() 포함 여부"),
    db: Session = Depends(get_db),
):
    query = db.query(Perfume)

    # 텍스트 필터
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Perfume.name.ilike(like), Perfume.brand_name.ilike(like)))

    # 브랜드 필터
    if brand_id:
        query = query.filter(Perfume.brand_id == uuid_hex_to_bytes(brand_id))

    # 성별 필터
    if gender:
        query = query.filter(Perfume.gender == gender)

    # 어코드 필터(JSON 배열에 요소 포함)
    # MySQL: JSON_CONTAINS(main_accords, '["woody"]')
    if accords:
        for acc in [a.strip() for a in accords.split(",") if a.strip()]:
            query = query.filter(func.json_contains(Perfume.main_accords, f'["{acc}"]'))

    # 노트 필터(top/middle/base/general 중 하나라도 매칭)
    # MySQL: JSON_SEARCH(path, 'one', 'Bergamot') IS NOT NULL
    if notes:
        for nt in [n.strip() for n in notes.split(",") if n.strip()]:
            query = query.filter(
                or_(
                    func.json_search(Perfume.top_notes, 'one', nt) != None,
                    func.json_search(Perfume.middle_notes, 'one', nt) != None,
                    func.json_search(Perfume.base_notes, 'one', nt) != None,
                    func.json_search(Perfume.general_notes, 'one', nt) != None,
                )
            )

    # 정렬
    if sort == "popular":
        query = query.order_by(Perfume.view_count.desc(), Perfume.wish_count.desc(), Perfume.id.desc())
    elif sort == "recent":
        query = query.order_by(Perfume.created_at.desc(), Perfume.id.desc())
    else:
        # relevance: 간단 가중치 점수(이름/브랜드 매치 + 인기 보정)
        if q:
            score = (
                func.if_(Perfume.name.ilike(f"%{q}%"), 10, 0) +
                func.if_(Perfume.brand_name.ilike(f"%{q}%"), 5, 0) +
                func.least(Perfume.view_count, 100) * 0.01 +
                func.least(Perfume.wish_count, 100) * 0.02
            )
        else:
            score = (
                func.least(Perfume.view_count, 100) * 0.01 +
                func.least(Perfume.wish_count, 100) * 0.02
            )
        query = query.order_by(score.desc(), Perfume.created_at.desc(), Perfume.id.desc())

    total = None
    if include_total:
        # count()는 비싸므로 요청 시에만 수행
        total = query.count()

    items = query.offset(offset).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": uuid_bytes_to_hex(p.id),
                "name": p.name,
                "brand_name": p.brand_name,
                "image_url": p.image_url,
                "gender": p.gender,
                "price": float(p.price) if p.price is not None else None,
                "currency": p.currency,
                "main_accords": p.main_accords,
                "view_count": p.view_count,
                "wish_count": p.wish_count,
            }
            for p in items
        ],
    }