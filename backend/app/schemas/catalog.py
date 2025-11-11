# app/schemas/catalog.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class PerfumeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: bytes # binary(16)은 bytes로 처리
    name: str
    brand_id: bytes # binary(16)은 bytes로 처리
    # brand_name: Optional[str] = None  # 👈 주석 처리
    image_url: Optional[str] = None

class PerfumeDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: bytes
    name: str
    brand_id: bytes
    # brand_name: Optional[str] = None  # 👈 주석 처리
    image_url: Optional[str] = None
    gender: Optional[str] = None
    price: Optional[float] = None  # Decimal → float
    longevity: Optional[float] = None # Decimal(5, 2) → float
    sillage: Optional[float] = None # Decimal(5, 2) → float
    
    # ❗ 모든 JSON 타입 필드를 임시로 주석 처리합니다.
    # main_accords: Optional[List[str]] = None
    # main_accords_percentage: Optional[Dict[str, str]] = None
    # top_notes: Optional[List[Dict[str, Any]]] = None
    # middle_notes: Optional[List[Dict[str, Any]]] = None
    # base_notes: Optional[List[Dict[str, Any]]] = None
    # season_ranking: Optional[List[Dict[str, float]]] = None
    # occasion_ranking: Optional[List[Dict[str, float]]] = None
    # purchase_url: Optional[str] = None