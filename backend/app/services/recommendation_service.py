import os
import json
from typing import List, Dict, Any, Optional

# SQLAlchemy 모듈 임포트
from sqlalchemy import create_engine, Column, Integer, String, Float, or_
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm.session import Session
import dotenv 
import random

# =========================================================================
# 1. 설정 및 모델 정의 (db_profiler_script.py와 동일하게 설정)
# =========================================================================

# 환경 변수 로드
dotenv.load_dotenv(dotenv_path='../../.env')

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("오류: 환경 변수 DATABASE_URL을 찾을 수 없습니다.")
    # 실제 FastAPI 서비스에서는 이 부분이 Config/Settings에서 처리됩니다.
    exit(1)

if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://")

Base = declarative_base()

class Perfume(Base):
    __tablename__ = 'perfume' # 단수형 'perfume' 테이블 사용
    
    id = Column(Integer, primary_key=True)
    # 데이터베이스에 존재하는 다른 컬럼들 (예시)
    name = Column(String) 
    brand_id = Column(Integer, name='brand_id')
    brand_name = Column(String, name='brand_name') # routes/pbti.py에서 Brand.name 대신 이 컬럼을 사용한다고 가정
    
    main_accords = Column(String) 
    top_notes = Column(String)
    middle_notes = Column(String)
    base_notes = Column(String)

    # PBTI 관련 컬럼
    pbti_type = Column(String(4))
    F_W_Score = Column(Float)
    L_H_Score = Column(Float)
    S_P_Score = Column(Float)
    N_M_Score = Column(Float)

# =========================================================================
# 2. 추천 로직 함수 (함수 이름 통일 및 LIKE 패턴 수정)
# =========================================================================

def perfume_to_dict(perfume: Perfume) -> Dict[str, Any]:
    """SQLAlchemy Perfume 객체를 JSON 응답을 위한 딕셔너리로 변환합니다."""
    return {
        "id": perfume.id,
        "name": perfume.name,
        "brand": perfume.brand_name,
        "pbti_type": perfume.pbti_type,
        "F_W_Score": perfume.F_W_Score,
        "L_H_Score": perfume.L_H_Score,
        "S_P_Score": perfume.S_P_Score,
        "N_M_Score": perfume.N_M_Score,
        # ... 필요한 다른 정보 추가
    }

def get_pbti_recommendations_by_type(db: Session, user_pbti_type: str, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """
    사용자의 PBTI 유형을 기반으로 5가지 종류의 향수 추천을 제공합니다.
    
    (참고: 기존 함수 이름 'get_pbti_recommendations'를 'get_pbti_recommendations_by_type'로 변경하여
    routes/pbti.py의 호출 함수 이름과 일치시켰습니다.)
    

    Args:
        db: SQLAlchemy 세션 객체.
        user_pbti_type: 사용자의 4글자 PBTI 유형 문자열 (예: "FWSP").
        limit: 각 카테고리별 최대 추천 개수.

    Returns:
        5가지 추천 목록을 담은 딕셔너리.
    """
    if len(user_pbti_type) != 4:
        raise ValueError("PBTI 유형은 4글자여야 합니다 (예: 'FWSP').")
        
    recommendations = {}
    
    # PBTI 축 분해
    axis_1 = user_pbti_type[0] # F/W
    axis_2 = user_pbti_type[1] # L/H
    axis_3 = user_pbti_type[2] # S/P
    axis_4 = user_pbti_type[3] # N/M

    # --- 1. 완벽 일치 (Perfect Match) ---
    # 사용자의 4글자 PBTI 타입과 완벽히 일치하는 향수
    perfect_match_query = db.query(Perfume).filter(
        Perfume.pbti_type == user_pbti_type
    )
    perfect_match_results = perfect_match_query.limit(limit).all()
    recommendations["perfect_match"] = [perfume_to_dict(p) for p in perfect_match_results]
    print(f"1. 완벽 일치 ({user_pbti_type}) {len(perfect_match_results)}개 조회 완료.")


    # --- 2. 첫 번째 축 (F/W) 일치 ---
    # PBTI 유형의 첫 글자만 일치하는 향수 (예: F***)
    axis1_match_query = db.query(Perfume).filter(
        Perfume.pbti_type.like(f"{axis_1}___")
    ).filter(
        Perfume.pbti_type != user_pbti_type # 완벽 일치는 제외하여 다양성 확보
    )
    axis1_match_results = axis1_match_query.limit(limit).all()
    recommendations["axis_1_match"] = [perfume_to_dict(p) for p in axis1_match_results]
    print(f"2. 첫 번째 축 ({axis_1}**) 일치 {len(axis1_match_results)}개 조회 완료.")


    # --- 3. 두 번째 축 (L/H) 일치 ---
    # PBTI 유형의 두 번째 글자만 일치하는 향수 (예: *L**)
    axis2_match_query = db.query(Perfume).filter(
        Perfume.pbti_type.like(f"_{axis_2}__")
    ).filter(
        Perfume.pbti_type != user_pbti_type
    )
    axis2_match_results = axis2_match_query.limit(limit).all()
    recommendations["axis_2_match"] = [perfume_to_dict(p) for p in axis2_match_results]
    print(f"3. 두 번째 축 (*{axis_2}**) 일치 {len(axis2_match_results)}개 조회 완료.")


    # --- 4. 세 번째 축 (S/P) 일치 ---
    # PBTI 유형의 세 번째 글자만 일치하는 향수 (예: **S*)
    axis3_match_query = db.query(Perfume).filter(
        Perfume.pbti_type.like(f"__{axis_3}_") # FIX: 3번째 글자이므로 언더바 2개로 수정 (원래: ___S_)
    ).filter(
        Perfume.pbti_type != user_pbti_type
    )
    axis3_match_results = axis3_match_query.limit(limit).all()
    recommendations["axis_3_match"] = [perfume_to_dict(p) for p in axis3_match_results]
    print(f"4. 세 번째 축 (**{axis_3}*) 일치 {len(axis3_match_results)}개 조회 완료.")


    # --- 5. 네 번째 축 (N/M) 일치 ---
    # PBTI 유형의 네 번째 글자만 일치하는 향수 (예: ***N)
    axis4_match_query = db.query(Perfume).filter(
        Perfume.pbti_type.like(f"___{axis_4}") # FIX: 4번째 글자이므로 언더바 3개로 수정 (원래: ____N)
    ).filter(
        Perfume.pbti_type != user_pbti_type
    )
    axis4_match_results = axis4_match_query.limit(limit).all()
    recommendations["axis_4_match"] = [perfume_to_dict(p) for p in axis4_match_results]
    print(f"5. 네 번째 축 (***{axis_4}) 일치 {len(axis4_match_results)}개 조회 완료.")
    
    return recommendations


# =========================================================================
# 3. 테스트 코드 (FastAPI에서 사용 시 이 부분은 제거하고 get_pbti_recommendations_by_type 함수를 임포트하여 사용)
# =========================================================================

if __name__ == "__main__":
    # 테스트용 사용자 PBTI 유형 (예시)
    TEST_PBTI = "FWSP" 
    
    print(f"--- PBTI 추천 서비스 테스트 시작 (유형: {TEST_PBTI}) ---")

    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db_session: Session = SessionLocal()
        
        # 추천 함수 실행
        result = get_pbti_recommendations_by_type(db_session, TEST_PBTI, limit=5)
        
        db_session.close()

        print("\n--- 추천 결과 요약 ---")
        print(f"1. 완벽 일치: {len(result['perfect_match'])}개")
        print(f"2. 축 1 ({TEST_PBTI[0]}***) 일치: {len(result['axis_1_match'])}개")
        print(f"3. 축 2 (*{TEST_PBTI[1]}**) 일치: {len(result['axis_2_match'])}개")
        print(f"4. 축 3 (**{TEST_PBTI[2]}*) 일치: {len(result['axis_3_match'])}개")
        print(f"5. 축 4 (***{TEST_PBTI[3]}) 일치: {len(result['axis_4_match'])}개")
        
        # 첫 번째 카테고리 예시 출력
        if result['perfect_match']:
            print("\n[완벽 일치 추천 예시 1개]:")
            print(json.dumps(result['perfect_match'][0], indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"\n테스트 중 오류 발생: {e}")