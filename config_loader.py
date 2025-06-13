import requests
import json
import os
import time
from typing import Optional, Dict

class WebConfigLoader:
    def __init__(self, web_url: str, password: str):
        self.web_url = web_url
        self.password = password
        self.config_cache = None
        self.last_update = 0
        self.cache_ttl = 60  # 1분 캐시
    
    def get_config(self) -> Optional[Dict]:
        """웹페이지에서 봇 설정을 가져옵니다."""
        current_time = time.time()
        
        # 캐시된 설정이 있고 아직 유효하다면 반환
        if (self.config_cache and 
            current_time - self.last_update < self.cache_ttl):
            return self.config_cache
        
        try:
            # GitHub Pages용 CORS 우회 방법들 시도
            methods = [
                self._try_fetch_with_params,
                self._try_fetch_jsonp,
                self._try_fetch_direct
            ]
            
            for method in methods:
                try:
                    bots = method()
                    if bots and len(bots) > 0:
                        # 첫 번째 봇 설정 사용
                        self.config_cache = bots[0]
                        self.last_update = current_time
                        print(f"✅ Web config loaded: {self.config_cache.get('projectName', 'Unknown')}")
                        return self.config_cache
                except Exception as e:
                    print(f"⚠️ Method failed: {e}")
                    continue
            
            print("⚠️ No bot configurations found on web")
            return None
                
        except Exception as e:
            print(f"❌ Error loading config from web: {e}")
            return None
    
    def _try_fetch_with_params(self):
        """URL 파라미터로 시도"""
        response = requests.get(
            f"{self.web_url}/config.json",
            params={"password": self.password},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    
    def _try_fetch_jsonp(self):
        """JSONP 방식으로 시도"""
        response = requests.get(
            f"{self.web_url}/config.jsonp",
            timeout=10
        )
        if response.status_code == 200:
            # JSONP 응답에서 JSON 추출
            text = response.text
            if 'window.botConfigCallback' in text:
                # 간단한 파싱 (실제로는 더 안전한 방법 사용)
                import json
                import re
                match = re.search(r'window\.botConfigCallback\s*&&\s*window\.botConfigCallback\s*\(\s*(\[.*?\])\s*\)', text)
                if match:
                    return json.loads(match.group(1))
        return None
    
    def _try_fetch_direct(self):
        """직접 요청 (CORS 허용된 경우)"""
        response = requests.get(
            f"{self.web_url}/api.js",
            timeout=10
        )
        # 이 방법은 실제 구현에서는 더 복잡할 수 있음
        return None
    
    def get_env_vars(self) -> Dict[str, str]:
        """봇 설정을 환경변수 형태로 반환합니다."""
        config = self.get_config()
        if not config:
            return {}
        
        # SSH 호스트와 포트 분리
        ssh_host = config.get('sshHost', 'localhost:22')
        if ':' in ssh_host:
            host, port = ssh_host.split(':', 1)
        else:
            host, port = ssh_host, '22'
        
        env_vars = {
            'TELEGRAM_BOT_TOKEN': config.get('botToken', ''),
            'TELEGRAM_CHAT_ID': config.get('chatId', ''),
            'SSH_HOST': host,
            'SSH_PORT': port,
            'SSH_USERNAME': config.get('sshUsername', ''),
            'SSH_PASSWORD': config.get('sshPassword', ''),
            'ALLOWED_USERS': config.get('chatId', ''),
            'MAX_OUTPUT_LENGTH': '4000',
            'WORKING_DIR': config.get('workingDir', '/root'),
            'CLAUDE_CODE_PATH': '/usr/local/bin/claude'
        }
        
        return env_vars
    
    def validate_config(self) -> bool:
        """필수 설정이 모두 있는지 확인합니다."""
        config = self.get_config()
        if not config:
            return False
        
        required_fields = ['botToken', 'chatId', 'sshHost', 'sshUsername']
        missing_fields = []
        
        for field in required_fields:
            if not config.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required config fields: {missing_fields}")
            return False
        
        return True

# 웹 설정으로 환경변수 설정하는 함수
def load_web_config_as_env(web_url: str, password: str) -> bool:
    """웹 설정을 로드하여 환경변수로 설정합니다."""
    loader = WebConfigLoader(web_url, password)
    
    if not loader.validate_config():
        return False
    
    env_vars = loader.get_env_vars()
    
    # 환경변수로 설정
    for key, value in env_vars.items():
        os.environ[key] = str(value)
        print(f"🔧 Set {key}={value[:10]}{'...' if len(value) > 10 else ''}")
    
    return True