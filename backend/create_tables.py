import os
import sys
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine
from app.models.base import Base # Base 모델을 가져옵니다.

# sys.path 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# .env 로드
load_dotenv(find_dotenv(), override=False)

# 환경 변수에서 DB URL 가져오기
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("FATAL: DATABASE_URL 환경 변수를 찾을 수 없습니다.")
    sys.exit(1)

def create_all_tables():
    """모든 SQLAlchemy 모델을 기반으로 테이블을 생성합니다."""
    try:
        print(f"Connecting to DB using URL: {DATABASE_URL.split('@')[-1]}")
        engine = create_engine(DATABASE_URL)
        
        # 🚨 여기서 모델에 정의된 모든 테이블을 생성합니다. (UUID 로직 포함)
        Base.metadata.create_all(engine)
        
        print("✅ Success: All tables created successfully based on current models.")
        
    except Exception as e:
        print(f"❌ Error during table creation: {type(e).__name__}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # app.models 내의 모든 모델을 로드하여 Base.metadata에 등록해야 합니다.
    # 이 파일을 실행하기 전에 __init__.py 등을 통해 모든 모델이 import되었는지 확인해주세요.
    # 안전을 위해 모든 모델을 임시로 로드합니다. (이 과정은 이미 SQLAlchemy가 처리할 수도 있습니다.)
    from app.models.brand import Brand
    from app.models.perfume import Perfume
    # 필요한 경우 다른 모델도 추가 import
    # from app.models.note import Note # 예시
    
    create_all_tables()