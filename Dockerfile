FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 SSH 클라이언트 설치
RUN apt-get update && apt-get install -y \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY telegram_terminal_bot_persistent.py .
COPY config_loader.py .

# 비루트 사용자 생성
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# 애플리케이션 실행
CMD ["python", "telegram_terminal_bot_persistent.py"]