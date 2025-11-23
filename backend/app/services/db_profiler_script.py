import os
import json
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# .env 파일 로드를 위해 dotenv 라이브러리를 가져옵니다.
import dotenv 

# A. 계산 로직이 있는 파일에서 함수를 임포트합니다.
try:
    from perfume_pbti_calculator import calculate_pbti_affinity
except ImportError:
    print("오류: 'perfume_pbti_calculator.py' 파일을 찾거나 임포트할 수 없습니다.")
    print("두 파일이 같은 디렉토리에 있는지 확인하십시오.")
    exit(1)


# =========================================================================
# 1. DB 연결 및 모델 정의
# =========================================================================

# B. .env 파일 로드 (스크립트 위치: backend/app/services/)
# .env 파일이 backend/ 에 있으므로 상대 경로 '../../.env'를 사용합니다.
# .env 파일 로드 후, 환경 변수를 os.environ에서 사용할 수 있게 됩니다.
dotenv.load_dotenv(dotenv_path='../../.env')

# .env 파일에서 DATABASE_URL을 읽어옵니다.
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("오류: 환경 변수 DATABASE_URL을 찾을 수 없습니다.")
    print(".env 파일에 'DATABASE_URL=...' 항목이 있는지 확인하십시오.")
    exit(1)

# MySQL URL 포맷 변환 (pymysql 드라이버 사용 가정)
if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://")

Base = declarative_base()

class Perfume(Base):
    # !!! 이 부분을 'perfume'으로 수정했습니다. !!!
    __tablename__ = 'perfume' 
    
    id = Column(Integer, primary_key=True)
    # DB에 저장된 원본 데이터 컬럼 (JSON 문자열 가정)
    main_accords = Column(String) 
    top_notes = Column(String)
    middle_notes = Column(String)
    base_notes = Column(String)

    # 마이그레이션으로 추가한 PBTI 점수 컬럼
    pbti_type = Column(String(4))
    F_W_Score = Column(Float)
    L_H_Score = Column(Float)
    S_P_Score = Column(Float)
    N_M_Score = Column(Float)
    

# =========================================================================
# 2. 메인 실행 함수
# =========================================================================

def profile_and_update_db():
    # 보안상 비밀번호를 제외한 DB 연결 정보만 표시
    conn_info = DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL
    print(f"DB 연결 시도: {conn_info}")
    
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        Session = sessionmaker(bind=engine)
        session = Session()
    except Exception as e:
        print(f"DB 연결 실패: {e}")
        return

    print("전체 향수 데이터 조회 중...")
    try:
        # 수정된 테이블 이름으로 쿼리 시도
        perfumes = session.query(Perfume).all()
        
        total_count = len(perfumes)
        update_count = 0
        
        print(f"총 {total_count}개의 향수 데이터를 찾았습니다. PBTI 점수 계산을 시작합니다.")

        for perfume in perfumes:
            try:
                # Perfume 객체를 딕셔너리로 변환하여 계산 함수에 전달
                perfume_data = {
                    'main_accords': perfume.main_accords,
                    'top_notes': perfume.top_notes,
                    'middle_notes': perfume.middle_notes,
                    'base_notes': perfume.base_notes
                }
                
                # 1. PBTI 점수 계산 (임포트된 함수 사용)
                pbti_results = calculate_pbti_affinity(perfume_data)
                
                # 2. DB 객체에 결과 업데이트
                perfume.pbti_type = pbti_results["pbti_type"]
                perfume.F_W_Score = pbti_results["F_W_Score"]
                perfume.L_H_Score = pbti_results["L_H_Score"]
                perfume.S_P_Score = pbti_results["S_P_Score"]
                perfume.N_M_Score = pbti_results["N_M_Score"]
                
                update_count += 1
                
                if update_count % 100 == 0:
                    # 100개마다 커밋하여 중간에 오류가 나도 작업이 날아가지 않도록 합니다.
                    session.commit()
                    print(f"-> {update_count} / {total_count}개 처리 및 중간 커밋 완료.")
            
            except Exception as e:
                # 특정 향수 처리 중 오류 발생 시 롤백하지 않고 해당 향수 ID를 출력
                print(f"경고: ID {perfume.id} 향수 데이터 처리 중 오류 발생: {e}. 건너뜁니다.")
                # 다음 향수로 넘어갑니다.

        # 최종 커밋
        session.commit()
        print(f"==================================================")
        print(f"성공: 총 {update_count}개의 향수 PBTI 점수 업데이트 완료.")
        print(f"==================================================")

    except Exception as e:
        session.rollback()
        print(f"데이터 조회 또는 전체 프로세스 중 치명적인 오류 발생: {e}")
        
    finally:
        session.close()

if __name__ == "__main__":
    profile_and_update_db()