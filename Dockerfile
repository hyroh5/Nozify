# 1. Python 베이스 이미지 (slim + Debian)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 2. OpenCV + Tesseract가 필요로 하는 시스템 라이브러리 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    tesseract-ocr \
 && rm -rf /var/lib/apt/lists/*

# 3. 작업 디렉토리
WORKDIR /app

# 4. 파이썬 의존성 설치 (루트 requirements.txt 사용)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 5. 나머지 코드 복사
COPY . .

# 6. FastAPI 앱 실행 (엔트리포인트 위치에 맞게 수정)
# 지금 구조상 app/main.py 에 app 이 있다고 가정
ENV PORT=8080
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
