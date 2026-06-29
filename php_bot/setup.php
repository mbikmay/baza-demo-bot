<?php

declare(strict_types=1);

$config = require __DIR__ . '/config.php';

function tg(string $method, array $params): array
{
    global $config;
    $url = 'https://api.telegram.org/bot' . $config['bot_token'] . '/' . $method;
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
        CURLOPT_POSTFIELDS => json_encode($params, JSON_UNESCAPED_UNICODE),
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_IPRESOLVE => CURL_IPRESOLVE_V4,
    ]);
    $response = curl_exec($ch);
    curl_close($ch);
    return json_decode((string) $response, true) ?: [];
}

$results = [];
$results['setWebhook'] = tg('setWebhook', ['url' => $config['webhook_url']]);
$results['setMyCommands'] = tg('setMyCommands', [
    'commands' => [
        ['command' => 'start', 'description' => 'Запустить демо'],
        ['command' => 'book', 'description' => 'Открыть бронирование'],
        ['command' => 'support', 'description' => 'Связаться с поддержкой'],
    ],
]);
$results['setChatMenuButton'] = tg('setChatMenuButton', [
    'menu_button' => ['type' => 'commands'],
]);

header('Content-Type: application/json; charset=utf-8');
echo json_encode($results, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
