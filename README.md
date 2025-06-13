# DevBot - Telegram Terminal Manager

텔레그램을 통해 원격 터미널을 관리하고 개발 작업을 수행할 수 있는 봇입니다.

## 🚀 Features

- **영구 세션 관리**: `/stop` 명령 전까지 세션 유지
- **원격 터미널 접속**: SSH를 통한 안전한 연결
- **다중 프로젝트 관리**: 여러 프로젝트 동시 관리
- **Claude Code 통합**: AI 도우미 기능
- **웹 기반 설정 관리**: GitHub Pages를 통한 쉬운 설정

## 📋 Quick Start

### 1. 봇 설정하기
[설정 페이지](https://bzjay53.github.io/devbot/)에서 봇을 설정하세요.

### 2. 필요한 패키지 설치
```bash
pip install python-telegram-bot python-dotenv paramiko
```

### 3. 봇 실행
```bash
python telegram_terminal_bot_persistent.py
```

## 🔧 Configuration

`.env` 파일 예시:
```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TELEGRAM_CHAT_ID=YOUR_CHAT_ID_HERE

# SSH Configuration
SSH_HOST=localhost
SSH_PORT=22
SSH_USERNAME=root
SSH_PASSWORD=

# Project Settings
WORKING_DIR=/root/project
```

## 📱 Commands

- `/start` - 세션 시작
- `/stop` - 세션 종료
- `/claude <query>` - Claude Code에 질문
- 텍스트 입력 - 터미널 명령 실행

## 🔒 Security

- 사용자 ID 기반 인증
- SSH 암호화 연결
- 환경 변수를 통한 민감 정보 관리

## 📝 License

MIT License