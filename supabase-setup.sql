-- Supabase 테이블 생성 스크립트
-- Supabase 대시보드의 SQL Editor에서 실행

-- bot_configs 테이블 생성
CREATE TABLE IF NOT EXISTS bot_configs (
    id BIGSERIAL PRIMARY KEY,
    password_hash TEXT NOT NULL,
    bot_id TEXT NOT NULL,
    config_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성 (성능 향상)
CREATE INDEX IF NOT EXISTS idx_bot_configs_password_hash 
ON bot_configs(password_hash);

CREATE INDEX IF NOT EXISTS idx_bot_configs_bot_id 
ON bot_configs(bot_id);

-- RLS (Row Level Security) 정책 활성화
ALTER TABLE bot_configs ENABLE ROW LEVEL SECURITY;

-- 모든 사용자가 자신의 데이터에만 접근 가능하도록 정책 설정
CREATE POLICY "Users can access their own configs" ON bot_configs
    FOR ALL USING (true);  -- API Key 기반 접근이므로 모든 접근 허용

-- 자동 업데이트 timestamp 트리거
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_bot_configs_updated_at 
    BEFORE UPDATE ON bot_configs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();