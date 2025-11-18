from typing import Optional, List, Any
from pydantic import BaseModel, Field

# ----------------------------------------------------
# 1. PerfumeListResponse: 목록에서 보여줄 기본 정보
# ----------------------------------------------------
class PerfumeBase(BaseModel):
    """향수 목록 조회 시 반환될 기본 데이터 스키마"""
    id: str = Field(..., description="향수 고유 UUID (바이너리 데이터를 문자열로 변환)")
    name: str = Field(..., description="향수 이름")
    brand_name: Optional[str] = Field(None, description="브랜드 이름")
    image_url: Optional[str] = Field(None, description="이미지 URL")
    gender: Optional[str] = Field(None, description="성별 (예: Male, Female, Unisex)")
    price: Optional[float] = Field(None, description="가격")
    longevity: Optional[float] = Field(None, description="지속력 점수")
    sillage: Optional[float] = Field(None, description="확산력 점수")
    
    # JSON 필드는 조회 시 List[str] 또는 Dict[str, Any] 형태로 반환됨
    main_accords: Optional[List[str]] = Field(None, description="주요 어코드 목록")

    class Config:
        # DB 모델 객체에서 Pydantic 모델을 생성할 수 있도록 허용
        from_attributes = True

# ----------------------------------------------------
# 2. PerfumeDetailResponse: 상세 페이지에서 보여줄 모든 정보
# ----------------------------------------------------
class PerfumeDetail(PerfumeBase):
    """향수 상세 정보 조회 시 반환될 확장 스키마"""
    # 추가 필드
    general_notes: Optional[List[str]] = Field(None, description="전체 노트 목록")
    main_accords_percentage: Optional[dict] = Field(None, description="주요 어코드 백분율")
    season_ranking: Optional[dict] = Field(None, description="계절 랭킹")
    occasion_ranking: Optional[dict] = Field(None, description="상황 랭킹")
    fragella_id: Optional[str] = Field(None, description="외부 소스 ID")
    
    # 카운터 정보
    view_count: int = Field(0, description="조회수")
    wish_count: int = Field(0, description="찜하기 수")

# ----------------------------------------------------
# 3. API Paging Response
# ----------------------------------------------------
class PaginatedPerfumes(BaseModel):
    """향수 목록 조회 API의 페이징 응답 구조"""
    total_count: int = Field(..., description="전체 향수 개수")
    limit: int = Field(..., description="페이지당 항목 수")
    offset: int = Field(..., description="현재 오프셋 (페이지 번호 대신 사용)")
    perfumes: List[PerfumeBase] = Field(..., description="현재 페이지의 향수 목록")