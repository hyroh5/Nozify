from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import Dict, Any, List, Optional
import uuid # UUID 처리용 모듈 추가
import decimal # DECIMAL 타입 처리를 위해 추가

from app.core.db import get_db
from app.models.perfume import Perfume 
# Pydantic 스키마는 타입 힌트용으로만 남겨두고 response_model에서 제거되었습니다.
from app.schemas.catalog import PerfumeSummary, PerfumeDetail # 이 스키마는 타입 힌트 용으로만 사용됩니다.

router = APIRouter(prefix="/catalog", tags=["catalog"])

# --- Helper function for serialization ---
def serialize_perfume_detail(p: Perfume) -> Dict[str, Any]:
    """Perfume ORM 객체를 상세 정보 딕셔너리로 변환 (BINARY/DECIMAL 처리 포함)"""
    
    # DECIMAL 필드 변환 헬퍼 (Decimal 객체를 float으로 변환)
    def to_float(value):
        if value is None:
            return None
        # Decimal 객체일 경우 float으로 변환
        return float(value) if isinstance(value, decimal.Decimal) else float(value) 

    # BINARY(16) ID를 16진수 문자열로 변환
    # Perfume 모델의 id는 BINARY(16)이므로 .hex()를 사용합니다.
    id_hex = p.id.hex() if p.id else None
    brand_id_hex = p.brand_id.hex() if p.brand_id else None

    detail = {
        "id": id_hex,
        "brand_id": brand_id_hex,
        
        # 텍스트 및 속성
        "name": p.name,
        "brand_name": p.brand_name,
        "currency": p.currency,
        "image_url": p.image_url,
        "image_fallbacks": p.image_fallbacks, # JSON 필드는 이미 Python Dict/List
        "gender": p.gender,
        "fragella_id": p.fragella_id,
        "purchase_url": p.purchase_url,

        # 숫자 필드 (DECIMAL)
        "price": to_float(p.price),
        "longevity": to_float(p.longevity),
        "sillage": to_float(p.sillage),

        # JSON 타입 (노트 및 랭킹 데이터)
        # JSON 필드가 None일 경우를 대비하여 빈 리스트/딕셔너리로 초기화
        "main_accords": p.main_accords or [],
        "main_accords_percentage": p.main_accords_percentage or {},
        "top_notes": p.top_notes or [],
        "middle_notes": p.middle_notes or [],
        "base_notes": p.base_notes or [],
        "general_notes": p.general_notes or [],
        "season_ranking": p.season_ranking or {},
        "occasion_ranking": p.occasion_ranking or {},

        # 카운터 필드
        "view_count": p.view_count,
        "wish_count": p.wish_count,
        "purchase_count": p.purchase_count,

        # 타임스탬프 필드
        "created_at": p.created_at.isoformat() if p.created_at else None, # 날짜를 문자열로 변환
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        "last_synced_at": p.last_synced_at.isoformat() if p.last_synced_at else None,
        
        # 관계 필드 (현재 비활성화)
        # "brand": serialize_brand(p.brand) 
    }
    return detail


@router.get("/perfumes/{perfume_id}") 
def get_perfume(
    perfume_id: str = Path(..., min_length=32, max_length=32, description="32자리 16진수 Perfume ID"), 
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    특정 ID의 향수 상세 정보를 조회합니다.
    (404 에러 해결 및 BINARY ID 처리 로직 활성화)
    """
    try:
        # 16진수 문자열을 BINARY 타입으로 변환
        binary_id = bytes.fromhex(perfume_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Perfume ID format. Must be a 32-character hex string.")
    
    # 데이터베이스에서 단건 조회
    perfume = db.query(Perfume).filter(Perfume.id == binary_id).first()
    
    if not perfume:
        raise HTTPException(status_code=404, detail=f"Perfume with ID {perfume_id} not found.")

    # ORM 객체를 수동으로 직렬화하여 반환
    return serialize_perfume_detail(perfume)


@router.get("/perfumes") 
def list_perfumes(
    brand_id: str | None = Query(None, min_length=32, max_length=32, description="32자리 16진수 Brand ID"),
    gender: str | None = Query(None, description="성별 필터링 (예: Male, Female, Unisex)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    offset: int = Query(0, ge=0, description="조회 시작 오프셋"),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    
    # Perfume 모델을 쿼리합니다.
    q = db.query(Perfume)
        
    # 1. brand_id 필터링 로직 추가 (UUID 처리)
    if brand_id:
        try:
            brand_binary_id = bytes.fromhex(brand_id)
            q = q.filter(Perfume.brand_id == brand_binary_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid Brand ID format. Must be a 32-character hex string.")
            
    # 2. gender 필터링
    if gender:
        q = q.filter(Perfume.gender == gender)
        
    # 3. 정렬, 오프셋, 리밋 적용
    items = q.order_by(Perfume.created_at.desc()) \
             .offset(offset) \
             .limit(limit) \
             .all()
    
    result = []
    for p in items:
        # DB 객체를 Python Dictionary로 변환하며 직렬화 문제(BINARY, DECIMAL)를 수동으로 해결합니다.
        try:
            summary = {
                # BINARY(16) ID를 16진수 문자열로 변환합니다.
                "id": p.id.hex() if p.id else None,
                "brand_id": p.brand_id.hex() if p.brand_id else None,
                
                "name": p.name,
                "image_url": p.image_url,
                "gender": p.gender,
                
                # DECIMAL 필드를 float()으로 변환합니다.
                "price": float(p.price) if p.price is not None and isinstance(p.price, decimal.Decimal) else None,
            }
            result.append(summary)
        except Exception as e:
            # 처리 실패 시 로그를 남기고 해당 항목은 건너뜁니다.
            print(f"ERROR: Failed to process perfume object due to: {e}")
            continue
            
    return result