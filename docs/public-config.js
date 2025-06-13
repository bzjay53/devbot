// Public configuration endpoint
// Updated by web interface
window.getPublicBotConfig = function(password) {
    // 암호화된 설정 (실제로는 암호화 필요)
    const encryptedConfigs = {
        // password hash: encrypted config
    };
    
    const passwordHash = btoa(password);
    return encryptedConfigs[passwordHash] || null;
};