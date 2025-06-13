# 🚀 Netlify + Supabase 배포 가이드

**완벽한 모바일 원격 관리 시스템**

## 📋 준비사항

1. GitHub 계정
2. Netlify 계정
3. Supabase 계정
4. 텔레그램 봇 토큰

## 🗄️ 1. Supabase 설정

### 1.1 프로젝트 생성
1. [Supabase](https://supabase.com) 접속
2. "New Project" 클릭
3. 프로젝트 이름: `devbot-manager`
4. 데이터베이스 비밀번호 설정

### 1.2 테이블 생성
1. 프로젝트 대시보드 → SQL Editor
2. `supabase-setup.sql` 내용 복사 및 실행
3. "Run" 클릭

### 1.3 API 키 복사
1. Settings → API
2. 다음 정보 복사:
   - **Project URL**: `https://xxx.supabase.co`
   - **Anon public key**: `eyJ...`

## 🌐 2. Netlify 배포

### 2.1 저장소 연결
1. [Netlify](https://netlify.com) 로그인
2. "New site from Git" 클릭
3. GitHub 저장소 선택: `bzjay53/devbot`
4. 브랜치: `main`

### 2.2 빌드 설정
- **Build command**: `echo "Build complete"`
- **Publish directory**: `docs`

### 2.3 환경변수 설정
Site settings → Environment variables:

```
SUPABASE_URL = https://xxx.supabase.co
SUPABASE_ANON_KEY = eyJ...
```

### 2.4 배포 확인
- 배포 완료 후 URL 확인 (예: `https://devbot-manager.netlify.app`)

## 🤖 3. 봇 실행

### 3.1 환경변수 설정
```bash
export WEB_PASSWORD="your_chosen_password"
```

### 3.2 Docker 실행
```bash
cd /root/devbot
WEB_PASSWORD="your_password" docker-compose up -d
```

## 📱 4. 사용 방법

### 4.1 웹 설정
1. Netlify URL 접속
2. 원하는 비밀번호로 로그인
3. 봇 설정 추가:
   - Project Name: `My Dev Bot`
   - SSH Host: `localhost:22`
   - SSH Username: `root`
   - SSH Password: `your_server_password`
   - Bot Token: `@BotFather에서 받은 토큰`
   - Chat ID: `본인 텔레그램 ID`
   - Working Dir: `/root`

### 4.2 봇 연결 확인
- 텔레그램에서 봇에게 `/start` 메시지 전송
- 봇이 응답하면 연결 완료!

## 🔧 5. 고급 설정

### 5.1 여러 봇 관리
- 웹에서 여러 프로젝트 추가 가능
- 각각 다른 서버/설정 사용 가능

### 5.2 보안 강화
- 강력한 패스워드 사용
- SSH 키 기반 인증 권장
- 정기적인 패스워드 변경

## 🎯 완성!

✅ **모바일에서 완전 원격 관리**
✅ **실시간 개발 환경**  
✅ **Claude Code 통합**
✅ **확장 가능한 아키텍처**

---

🚀 **이제 어디서든 개발하세요!**