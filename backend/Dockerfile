FROM python:3.11-slim

# 1. OpenCV + Tesseract가 필요로 하는 시스템 라이브러리 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    tesseract-ocr \
  && rm -rf /var/lib/apt/lists/*

# 2. 작업 디렉토리 설정 (backend 컨텍스트 기준)
WORKDIR /app

# 3. 파이썬 의존성 설치
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 4. 앱 소스 복사
COPY . .

# 5. 로그 버퍼링 방지
ENV PYTHONUNBUFFERED=1

# 6. FastAPI 실행 (backend 안의 app/main.py)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
