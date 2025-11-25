# app/api/routes/recommendations_brand.py

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.api.deps import get_current_user_id
from app.models.user import User
from app.services.brand_recommendation_service import (
    get_user_top_brands,
    get_brand_perfumes_for_user,
)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/brands")
def recommend_brands_for_user(
    limit: int = Query(7, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id),  # 로그인 필수
) -> Dict[str, Any]:
    """
    3번 탭: '내가 자주 보는 브랜드 추천'
    - 사용자의 RecentView 기반으로 상위 브랜드 최대 7개 반환
    """
    user_id_bytes: bytes = current_user.id

    items = get_user_top_brands(db, user_id_bytes, limit=limit)

    return {
        "user_id": current_user.id.hex(),
        "count": len(items),
        "items": items,
    }


@router.get("/brands/{brand_id}")
def recommend_perfumes_in_brand_for_user(
    brand_id: str = Path(..., description="hex UUID 형식의 브랜드 ID"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id),  # 로그인 필수
) -> Dict[str, Any]:
    """
    3번 탭: 특정 브랜드 선택 시
    - 해당 브랜드 내 향수를 '사용자 취향 유사도' 순으로 정렬해서 최대 10개 반환
    """
    user_id_bytes: bytes = current_user.id

    try:
        # 단순 형식 체크
        bytes.fromhex(brand_id)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid brand_id hex")

    perfumes = get_brand_perfumes_for_user(
        db=db,
        user_id_bytes=user_id_bytes,
        brand_id_hex=brand_id,
        limit=limit,
    )

    return {
        "user_id": current_user.id.hex(),
        "brand_id": brand_id,
        "count": len(perfumes),
        "items": perfumes,
    }
