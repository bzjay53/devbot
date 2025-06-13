# 🔥 Firebase 설정 가이드

## 1. Firebase 프로젝트 생성

1. [Firebase Console](https://console.firebase.google.com) 접속
2. **"프로젝트 만들기"** 클릭
3. 프로젝트 이름: `tgdevbot-manager`
4. Google Analytics: 비활성화 (선택사항)
5. **"프로젝트 만들기"** 클릭

## 2. Firestore Database 설정

1. 왼쪽 메뉴에서 **"Firestore Database"** 클릭
2. **"데이터베이스 만들기"** 클릭
3. **프로덕션 모드**에서 시작
4. 위치: `asia-northeast3` (서울)
5. **"사용 설정"** 클릭

## 3. 보안 규칙 설정

Firestore Database → Rules 탭에서:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // bot_configs 컬렉션은 인증된 요청만 허용
    match /bot_configs/{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

## 4. Service Account 생성

1. **프로젝트 설정** (톱니바퀴 아이콘)
2. **"서비스 계정"** 탭
3. **"새 비공개 키 생성"** 클릭
4. JSON 파일 다운로드

## 5. 다운로드한 JSON 파일 내용

```json
{
  "type": "service_account",
  "project_id": "tgdevbot-manager",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxx@tgdevbot-manager.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "...",
  "token_uri": "...",
  "auth_provider_x509_cert_url": "...",
  "client_x509_cert_url": "..."
}
```

## 6. Netlify 환경변수 설정

Netlify Dashboard → Site settings → Environment variables:

### FIREBASE_SERVICE_ACCOUNT
- **Value**: 위 JSON 내용 전체를 **한 줄로** 복사
- 예시:
```
{"type":"service_account","project_id":"tgdevbot-manager",...}
```

### FIREBASE_DATABASE_URL
- **Value**: `https://tgdevbot-manager-default-rtdb.asia-southeast1.firebasedatabase.app`
- 프로젝트 설정에서 확인 가능

## 7. 함수 파일 변경

Netlify가 Firebase 함수를 사용하도록 설정:

1. `netlify/functions/bot-config.js` → `bot-config-supabase.js`로 이름 변경
2. `netlify/functions/bot-config-firebase.js` → `bot-config.js`로 이름 변경

## 8. 재배포

1. Netlify Dashboard → Deploys
2. **"Trigger deploy"** → **"Deploy site"**

## ✅ 완료!

이제 Firebase를 통해 봇 설정을 저장하고 관리할 수 있습니다!