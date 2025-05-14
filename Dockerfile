# Python 슬림 이미지 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY . .

# Cloud Run은 8080 포트 사용
ENV PORT=8080

# 앱 실행
CMD ["python", "main.py"]
