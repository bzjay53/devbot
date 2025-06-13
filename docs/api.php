<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

// 데이터 저장 파일 경로
$dataFile = 'bots_data.json';

// 비밀번호 검증
function verifyPassword($inputPassword) {
    $passwordFile = 'password.txt';
    if (!file_exists($passwordFile)) {
        return false;
    }
    $savedPassword = trim(file_get_contents($passwordFile));
    return base64_encode($inputPassword) === $savedPassword;
}

// 데이터 읽기
function readData() {
    global $dataFile;
    if (!file_exists($dataFile)) {
        return [];
    }
    $data = file_get_contents($dataFile);
    return json_decode($data, true) ?: [];
}

// 데이터 쓰기
function writeData($data) {
    global $dataFile;
    return file_put_contents($dataFile, json_encode($data, JSON_PRETTY_PRINT));
}

$method = $_SERVER['REQUEST_METHOD'];
$input = json_decode(file_get_contents('php://input'), true);

switch ($method) {
    case 'GET':
        // 봇 설정 조회
        if (isset($_GET['password'])) {
            if (verifyPassword($_GET['password'])) {
                echo json_encode(readData());
            } else {
                http_response_code(401);
                echo json_encode(['error' => 'Invalid password']);
            }
        } else {
            http_response_code(400);
            echo json_encode(['error' => 'Password required']);
        }
        break;
        
    case 'POST':
        // 비밀번호 설정 (첫 사용)
        if (isset($input['action']) && $input['action'] === 'set_password') {
            $passwordFile = 'password.txt';
            if (!file_exists($passwordFile)) {
                file_put_contents($passwordFile, base64_encode($input['password']));
                echo json_encode(['success' => true]);
            } else {
                http_response_code(400);
                echo json_encode(['error' => 'Password already set']);
            }
        }
        // 봇 설정 저장
        else if (isset($input['password']) && isset($input['bots'])) {
            if (verifyPassword($input['password'])) {
                writeData($input['bots']);
                echo json_encode(['success' => true]);
            } else {
                http_response_code(401);
                echo json_encode(['error' => 'Invalid password']);
            }
        } else {
            http_response_code(400);
            echo json_encode(['error' => 'Invalid request']);
        }
        break;
        
    default:
        http_response_code(405);
        echo json_encode(['error' => 'Method not allowed']);
        break;
}
?>