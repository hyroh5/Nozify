# 베이스 이미지
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# OpenCV + Tesseract가 필요로 하는 시스템 라이브러리 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    tesseract-ocr \
 && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리
WORKDIR /app

# 의존성 설치
# (레포 루트에 있는 requirements.txt 사용)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 나머지 코드 복사
COPY . .

# uvicorn 실행
# /app/app/main.py 에서 FastAPI 인스턴스가 app 이라고 가정
ENV PORT=8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
