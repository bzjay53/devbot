const admin = require('firebase-admin');

// Firebase Admin 초기화
let firebaseApp;
try {
  // Netlify 환경변수에서 Firebase 설정 가져오기
  const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT || '{}');
  
  if (!firebaseApp && serviceAccount.project_id) {
    firebaseApp = admin.initializeApp({
      credential: admin.credential.cert(serviceAccount),
      databaseURL: process.env.FIREBASE_DATABASE_URL
    });
  }
} catch (error) {
  console.error('Firebase initialization error:', error);
}

const db = firebaseApp ? admin.firestore() : null;

exports.handler = async (event, context) => {
  // CORS 헤더 설정
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  };

  // OPTIONS 요청 처리 (CORS preflight)
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: '',
    };
  }

  // Firebase 초기화 확인
  if (!db) {
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: 'Firebase not initialized' }),
    };
  }

  try {
    const { httpMethod, body, queryStringParameters } = event;
    
    switch (httpMethod) {
      case 'GET':
        return await getBotConfigs(queryStringParameters, headers);
      case 'POST':
        return await saveBotConfigs(JSON.parse(body), headers);
      case 'DELETE':
        return await deleteBotConfig(queryStringParameters, headers);
      default:
        return {
          statusCode: 405,
          headers,
          body: JSON.stringify({ error: 'Method not allowed' }),
        };
    }
  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: 'Internal server error' }),
    };
  }
};

// 봇 설정 조회
async function getBotConfigs(params, headers) {
  const { password } = params || {};
  
  if (!password) {
    return {
      statusCode: 400,
      headers,
      body: JSON.stringify({ error: 'Password required' }),
    };
  }

  // 비밀번호 해시 생성
  const passwordHash = Buffer.from(password).toString('base64');
  
  try {
    // Firestore에서 설정 조회
    const snapshot = await db.collection('bot_configs')
      .where('password_hash', '==', passwordHash)
      .get();

    const configs = [];
    snapshot.forEach(doc => {
      configs.push({
        id: doc.id,
        ...doc.data()
      });
    });

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify(configs),
    };
  } catch (error) {
    console.error('Database error:', error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: 'Database error' }),
    };
  }
}

// 봇 설정 저장
async function saveBotConfigs(body, headers) {
  const { password, bots } = body;
  
  if (!password || !bots) {
    return {
      statusCode: 400,
      headers,
      body: JSON.stringify({ error: 'Password and bots required' }),
    };
  }

  const passwordHash = Buffer.from(password).toString('base64');

  try {
    // 배치 작업 시작
    const batch = db.batch();
    
    // 기존 설정 삭제
    const existingDocs = await db.collection('bot_configs')
      .where('password_hash', '==', passwordHash)
      .get();
    
    existingDocs.forEach(doc => {
      batch.delete(doc.ref);
    });

    // 새 설정 추가
    bots.forEach(bot => {
      const docRef = db.collection('bot_configs').doc();
      batch.set(docRef, {
        password_hash: passwordHash,
        bot_id: bot.id,
        config_data: bot,
        created_at: admin.firestore.FieldValue.serverTimestamp(),
        updated_at: admin.firestore.FieldValue.serverTimestamp()
      });
    });

    // 배치 커밋
    await batch.commit();

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ success: true }),
    };
  } catch (error) {
    console.error('Database error:', error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: 'Database error' }),
    };
  }
}

// 봇 설정 삭제
async function deleteBotConfig(params, headers) {
  const { password, botId } = params || {};
  
  if (!password || !botId) {
    return {
      statusCode: 400,
      headers,
      body: JSON.stringify({ error: 'Password and botId required' }),
    };
  }

  const passwordHash = Buffer.from(password).toString('base64');

  try {
    // 삭제할 문서 찾기
    const snapshot = await db.collection('bot_configs')
      .where('password_hash', '==', passwordHash)
      .where('bot_id', '==', botId)
      .get();

    // 문서 삭제
    const batch = db.batch();
    snapshot.forEach(doc => {
      batch.delete(doc.ref);
    });
    
    await batch.commit();

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ success: true }),
    };
  } catch (error) {
    console.error('Database error:', error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: 'Database error' }),
    };
  }
}