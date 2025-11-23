from sqlalchemy import Column, Integer, String, ForeignKey, Float, DECIMAL, JSON, TIMESTAMP, func, UniqueConstraint, Index
from sqlalchemy.dialects.mysql import BINARY
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid

class Perfume(Base):
    __tablename__ = "perfume"
    __table_args__ = (
        UniqueConstraint("external_source", "external_id", name="uq_perfume_external"),
        Index("ix_perfume_brand_id", "brand_id"),
    )

    # --- 기본 키 및 외래 키 ---
    # BINARY(16) 타입 처리
    id = Column(BINARY(16), primary_key=True, default=lambda: uuid.uuid4().bytes, index=True)
    brand_id = Column(BINARY(16), ForeignKey("brand.id"), index=True) # MUL
    
    # --- 텍스트 및 속성 ---
    name = Column(String(255), nullable=False)
    brand_name = Column(String(100), nullable=True) 
    currency = Column(String(3), default="KRW", nullable=True)
    image_url = Column(String(255), nullable=True) 
    image_fallbacks = Column(JSON, nullable=True)
    gender = Column(String(20), nullable=True) # MUL
    fragella_id = Column(String(100), unique=True, nullable=True) # UNI
    purchase_url = Column(String(1024), nullable=True)
    source_url = Column(String(255), nullable=True)
    concentration = Column(String(50), nullable=True)
    external_source = Column(String(50), nullable=False, default="fragella")
    external_id = Column(String(100), nullable=False)

    # --- 숫자 타입 ---
    # DECIMAL(10, 2) 및 DECIMAL(5, 2) 타입 처리
    price = Column(DECIMAL(10, 2), nullable=True)
    longevity = Column(DECIMAL(5, 2), nullable=True)
    sillage = Column(DECIMAL(5, 2), nullable=True)

    # --- JSON 타입 (노트 및 랭킹 데이터) ---
    main_accords = Column(JSON, nullable=True)
    main_accords_percentage = Column(JSON, nullable=True)
    top_notes = Column(JSON, nullable=True)
    middle_notes = Column(JSON, nullable=True)
    base_notes = Column(JSON, nullable=True)
    general_notes = Column(JSON, nullable=True)
    season_ranking = Column(JSON, nullable=True)
    occasion_ranking = Column(JSON, nullable=True)

    # --- PBTI 프로파일 점수 컬럼 (새로 추가) ---
    # F/W (Fresh/Warm) 축 점수
    F_W_Score = Column(Float, default=0.0, nullable=True)
    # L/H (Light/Heavy) 축 점수
    L_H_Score = Column(Float, default=0.0, nullable=True)
    # S/P (Simple/Polymorphic) 축 점수
    S_P_Score = Column(Float, default=0.0, nullable=True)
    # N/M (Natural/Manmade) 축 점수
    N_M_Score = Column(Float, default=0.0, nullable=True)
    # 계산된 PBTI 타입 (예: FLSM)
    pbti_type = Column(String(4), default="", nullable=True)

    # --- 카운터 필드 ---
    view_count = Column(Integer, default=0, nullable=True)
    wish_count = Column(Integer, default=0, nullable=True)
    purchase_count = Column(Integer, default=0, nullable=True)

    # --- 타임스탬프 필드 ---
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now()) # on update CURRENT_TIMESTAMP
    last_synced_at = Column(TIMESTAMP, nullable=True)
    
    # --- 관계 설정 (InvalidRequestError 해결) ---
    # Brand 모델과의 관계
    brand = relationship("Brand", back_populates="perfumes")

    # PerfumeNote 모델과의 관계 (이전에 누락되어 500 에러를 유발했습니다)
    # PerfumeNote 모델의 back_populates가 'perfume'이라고 가정합니다.
    notes = relationship("PerfumeNote", back_populates="perfume")