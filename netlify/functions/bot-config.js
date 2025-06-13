const { createClient } = require('@supabase/supabase-js');

// Supabase 클라이언트 설정
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

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
    const { data, error } = await supabase
      .from('bot_configs')
      .select('*')
      .eq('password_hash', passwordHash);

    if (error) throw error;

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify(data || []),
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
    // 기존 설정 삭제
    await supabase
      .from('bot_configs')
      .delete()
      .eq('password_hash', passwordHash);

    // 새 설정 추가
    const configsToInsert = bots.map(bot => ({
      password_hash: passwordHash,
      bot_id: bot.id,
      config_data: bot,
      created_at: new Date().toISOString(),
    }));

    const { error } = await supabase
      .from('bot_configs')
      .insert(configsToInsert);

    if (error) throw error;

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
    const { error } = await supabase
      .from('bot_configs')
      .delete()
      .eq('password_hash', passwordHash)
      .eq('bot_id', botId);

    if (error) throw error;

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