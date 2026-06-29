<?php

declare(strict_types=1);

define('BOT_CRON', true);
require __DIR__ . '/bot.php';

$files = glob(__DIR__ . '/storage/users/*.json') ?: [];

foreach ($files as $file) {
    $state = json_decode((string) file_get_contents($file), true) ?: [];
    $chatId = (int) basename($file, '.json');

    if (($state['client_path_started'] ?? false) === true) {
        continue;
    }

    if (empty($state['auto_start_at']) || time() < (int) $state['auto_start_at']) {
        continue;
    }

    $state['client_path_started'] = true;
    saveState($chatId, $state);

    sendMessage(
        $chatId,
        'Автоматически запускаю путь клиента, чтобы вы могли посмотреть демо бронирования.',
        mainKeyboard($state['country'] ?? 'kz')
    );
    showClientPath($chatId, $state);
}
