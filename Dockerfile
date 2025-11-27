# 1. Python 3.11이 깔린 슬림한 리눅스 이미지 사용
FROM python:3.11-slim

# 2. 파이썬 관련 기본 설정 (로그 버퍼링 끄기 등)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. OpenCV + Tesseract에 필요한 시스템 라이브러리 설치
#    - libgl1, libglib2.0-0: OpenCV가 필요로 하는 그래픽 라이브러리
#    - tesseract-ocr: pytesseract가 내부에서 호출하는 실행 파일
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
 && rm -rf /var/lib/apt/lists/*

# 4. 작업 디렉토리 설정 (컨테이너 안에서 /app 폴더가 우리 프로젝트 루트가 됨)
WORKDIR /app

# 5. 파이썬 의존성 설치
#    먼저 requirements.txt만 복사해서 pip install 해준다.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 6. 나머지 모든 소스 코드 복사
COPY . .

# 7. Railway에서 PORT 환경변수를 넘겨주긴 하지만,
#    기본값 8000으로 세팅해둔다.
ENV PORT=8000

# 8. FastAPI 실행 명령
#    - app/main.py 안에 있는 FastAPI 인스턴스가 app이라고 가정 (이미 로그에서도 app.main:app 사용 중)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
