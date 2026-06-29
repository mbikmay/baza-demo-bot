<?php

declare(strict_types=1);

header('Content-Type: text/plain; charset=utf-8');

echo "PHP bot health check\n\n";

$configPath = __DIR__ . '/config.php';
$storagePath = __DIR__ . '/storage/users';

echo 'PHP version: ' . PHP_VERSION . "\n";
echo 'config.php: ' . (file_exists($configPath) ? 'OK' : 'MISSING') . "\n";
echo 'cURL: ' . (function_exists('curl_init') ? 'OK' : 'MISSING') . "\n";

if (!is_dir($storagePath)) {
    @mkdir($storagePath, 0775, true);
}

echo 'storage/users folder: ' . (is_dir($storagePath) ? 'OK' : 'MISSING') . "\n";
echo 'storage/users writable: ' . (is_writable($storagePath) ? 'OK' : 'NOT WRITABLE') . "\n";

if (!file_exists($configPath)) {
    echo "\nCreate config.php from config.example.php first.\n";
    exit;
}

$config = require $configPath;
$token = $config['bot_token'] ?? '';

echo 'bot_token: ' . ($token && $token !== 'PASTE_BOT_TOKEN_HERE' ? 'OK' : 'EMPTY') . "\n";
echo 'webhook_url: ' . (($config['webhook_url'] ?? '') ?: 'EMPTY') . "\n";
echo 'webapp_url: ' . (($config['webapp_url'] ?? '') ?: 'EMPTY') . "\n";

if (!$token || $token === 'PASTE_BOT_TOKEN_HERE' || !function_exists('curl_init')) {
    exit;
}

$url = 'https://api.telegram.org/bot' . $token . '/getWebhookInfo';
$ch = curl_init($url);
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_CONNECTTIMEOUT => 10,
    CURLOPT_TIMEOUT => 30,
    CURLOPT_IPRESOLVE => CURL_IPRESOLVE_V4,
]);
$response = curl_exec($ch);
$error = curl_error($ch);
curl_close($ch);

echo "\nTelegram getWebhookInfo:\n";
echo $response ?: ('ERROR: ' . $error);
echo "\n";
