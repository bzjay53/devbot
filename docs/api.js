// GitHub Pages용 클라이언트 사이드 API
class GitHubPagesAPI {
    constructor() {
        this.storageKey = 'devbot_configs';
        this.passwordKey = 'devbot_password';
    }
    
    // 비밀번호 검증
    verifyPassword(inputPassword) {
        const savedPassword = localStorage.getItem(this.passwordKey);
        if (!savedPassword) {
            return null; // 첫 사용
        }
        return btoa(inputPassword) === savedPassword;
    }
    
    // 첫 비밀번호 설정
    setPassword(password) {
        localStorage.setItem(this.passwordKey, btoa(password));
        return true;
    }
    
    // 봇 설정 조회
    getBots(password) {
        if (!this.verifyPassword(password)) {
            throw new Error('Invalid password');
        }
        const data = localStorage.getItem(this.storageKey);
        return data ? JSON.parse(data) : [];
    }
    
    // 봇 설정 저장
    saveBots(password, bots) {
        if (!this.verifyPassword(password)) {
            throw new Error('Invalid password');
        }
        localStorage.setItem(this.storageKey, JSON.stringify(bots));
        return true;
    }
    
    // 공개 API 엔드포인트 (CORS 우회용)
    async getPublicBots() {
        try {
            const data = localStorage.getItem(this.storageKey);
            return data ? JSON.parse(data) : [];
        } catch (error) {
            return [];
        }
    }
    
    // JSONP 파일 업데이트 (봇이 읽을 수 있도록)
    updateJSONP() {
        try {
            const bots = localStorage.getItem(this.storageKey);
            const data = bots ? JSON.parse(bots) : [];
            
            // 실제 환경에서는 GitHub API나 서버에 업데이트
            console.log('Bot config updated:', data);
            
            // localStorage에 공개 플래그 설정
            localStorage.setItem('devbot_public_config', JSON.stringify(data));
        } catch (error) {
            console.error('Failed to update JSONP:', error);
        }
    }
}

// 전역 API 인스턴스
window.devbotAPI = new GitHubPagesAPI();