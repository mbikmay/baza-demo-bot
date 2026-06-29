<?php

declare(strict_types=1);

error_reporting(E_ALL);
ini_set('display_errors', '0');

$logDir = __DIR__ . '/storage';
if (!is_dir($logDir)) {
    @mkdir($logDir, 0775, true);
}

function botLog(string $message): void
{
    @file_put_contents(
        __DIR__ . '/storage/error.log',
        '[' . date('Y-m-d H:i:s') . '] ' . $message . PHP_EOL,
        FILE_APPEND | LOCK_EX
    );
}

set_exception_handler(function (Throwable $exception): void {
    botLog('Exception: ' . $exception->getMessage() . ' in ' . $exception->getFile() . ':' . $exception->getLine());
});

register_shutdown_function(function (): void {
    $error = error_get_last();
    if ($error && in_array($error['type'], [E_ERROR, E_PARSE, E_CORE_ERROR, E_COMPILE_ERROR], true)) {
        botLog('Fatal: ' . $error['message'] . ' in ' . $error['file'] . ':' . $error['line']);
    }
});

if (!file_exists(__DIR__ . '/config.php')) {
    botLog('Missing config.php');
    http_response_code(500);
    exit('Missing config.php');
}

$config = require __DIR__ . '/config.php';

const STORAGE_DIR = __DIR__ . '/storage/users';

function api(string $method, array $params = []): array
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

function userFile(int $chatId): string
{
    if (!is_dir(STORAGE_DIR)) {
        mkdir(STORAGE_DIR, 0775, true);
    }
    return STORAGE_DIR . '/' . $chatId . '.json';
}

function loadState(int $chatId): array
{
    $file = userFile($chatId);
    if (!file_exists($file)) {
        return [];
    }
    return json_decode((string) file_get_contents($file), true) ?: [];
}

function saveState(int $chatId, array $state): void
{
    file_put_contents(
        userFile($chatId),
        json_encode($state, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT),
        LOCK_EX
    );
}

function countryInfo(string $country): array
{
    $countries = [
        'kz' => [
            'name' => 'Казахстан',
            'city' => 'Алматы',
            'currency' => '₸',
            'support' => '@baza_support_kz',
            'phone' => '+7 777 000 00 00',
            'location' => 'Казахстан, Алматинская область, 18 км от Капшагая, зона отдыха «Aq Samal Resort», участок 7',
            'about' => '«Aq Samal Resort» — уютная база отдыха рядом с водоёмом, где можно снять домик на выходные, отдохнуть с семьёй, пожарить шашлыки, сходить в баню и провести вечер на свежем воздухе.',
        ],
        'ru' => [
            'name' => 'Россия',
            'city' => 'Москва',
            'currency' => '₽',
            'support' => '@baza_support_ru',
            'phone' => '+7 999 000 00 00',
            'location' => 'Россия, Московская область, Истринский район, посёлок Лесное Озеро, база отдыха «Sosnovy Bereg», дом 4',
            'about' => '«Sosnovy Bereg» — загородная база отдыха среди леса, с тёплыми домиками, баней, беседками и спокойной атмосферой для семейных поездок, компаний и короткого отдыха за городом.',
        ],
    ];

    return $countries[$country] ?? $countries['kz'];
}

function housePrices(string $country): array
{
    return $country === 'ru'
        ? ['house_2' => 5000, 'house_4' => 7000, 'house_6' => 10000]
        : ['house_2' => 25000, 'house_4' => 35000, 'house_6' => 50000];
}

function houses(): array
{
    return [
        'house_2' => ['title' => 'Домик Comfort на 2 человека', 'capacity' => 2],
        'house_4' => ['title' => 'Домик Family на 4 человека', 'capacity' => 4],
        'house_6' => ['title' => 'Домик Grand на 6 человек', 'capacity' => 6],
    ];
}

function money(int $value, string $country): string
{
    return number_format($value, 0, '.', ' ') . ' ' . countryInfo($country)['currency'];
}

function formatDateText(?string $date): string
{
    if (!$date) {
        return 'не выбрано';
    }
    $time = strtotime($date);
    return $time ? date('d.m.Y', $time) : $date;
}

function sendMessage(int $chatId, string $text, ?array $replyMarkup = null): void
{
    $params = [
        'chat_id' => $chatId,
        'text' => $text,
        'parse_mode' => 'HTML',
    ];
    if ($replyMarkup) {
        $params['reply_markup'] = $replyMarkup;
    }
    api('sendMessage', $params);
}

function countryKeyboard(): array
{
    return [
        'inline_keyboard' => [
            [['text' => 'Казахстан', 'callback_data' => 'country:kz']],
            [['text' => 'Россия', 'callback_data' => 'country:ru']],
        ],
    ];
}

function salesKeyboard(): array
{
    return [
        'keyboard' => [
            [['text' => 'Протестировать бота']],
            [['text' => 'Что решает бот'], ['text' => 'Что можно настроить']],
            [['text' => 'Пример заявки админу'], ['text' => 'Связаться']],
            [['text' => 'Сменить страну']],
        ],
        'resize_keyboard' => true,
    ];
}

function mainKeyboard(string $country): array
{
    global $config;
    $separator = strpos($config['webapp_url'], '?') !== false ? '&' : '?';
    $url = $config['webapp_url'] . $separator . 'country=' . $country;

    return [
        'keyboard' => [
            [['text' => 'Выбрать даты', 'web_app' => ['url' => $url]]],
            [['text' => 'Цены'], ['text' => 'Адрес']],
            [['text' => 'Что есть на территории'], ['text' => 'Условия проживания']],
            [['text' => 'Контакты'], ['text' => 'Информация для гостя']],
            [['text' => 'Сменить страну']],
        ],
        'resize_keyboard' => true,
    ];
}

function finalBookingKeyboard(): array
{
    return [
        'inline_keyboard' => [
            [['text' => 'Имитировать бронь', 'callback_data' => 'pay:demo']],
            [['text' => 'Открыть поддержку', 'callback_data' => 'support:open']],
        ],
    ];
}

function ownerIntroText(): string
{
    return '<b>Демо чат-бота для базы отдыха</b>' . "\n\n"
        . 'Это пример бота, который можно адаптировать под вашу базу отдыха: добавить ваши домики, фотографии, цены, свободные даты, правила, контакты и способ оплаты.' . "\n\n"
        . '<b>Что можно сделать в демо:</b>' . "\n"
        . "• пройти путь гостя от выбора дат до брони;\n"
        . "• посмотреть, как выглядят домики и услуги;\n"
        . "• увидеть расчёт стоимости;\n"
        . "• получить пример инструкции после бронирования.\n\n"
        . 'Нажмите «Протестировать бота», чтобы посмотреть путь клиента.';
}

function benefitsText(): string
{
    return '<b>Что решает такой бот</b>' . "\n\n"
        . "<b>1. Больше прямых бронирований</b>\n"
        . "Гость может забронировать напрямую через Telegram. Это помогает меньше зависеть от агрегаторов, где комиссия может быть 15-20%.\n\n"
        . "<b>2. Меньше ручной переписки</b>\n"
        . "Бот сам отвечает на частые вопросы: цены, адрес, условия, что есть на территории, как добраться.\n\n"
        . "<b>3. Заявки не теряются</b>\n"
        . "Бот собирает имя, телефон, даты, количество гостей, домик и комментарий.\n\n"
        . "<b>4. Сбор базы гостей</b>\n"
        . "Контакты можно сохранять и потом использовать для акций, свободных дат и повторных продаж.\n\n"
        . "<b>5. Быстрее доводит до решения</b>\n"
        . "Гость сразу видит фото, даты, стоимость и следующий шаг.";
}

function customizationText(): string
{
    return '<b>Что можно настроить под вашу базу</b>' . "\n\n"
        . "• ваши домики, номера, беседки и услуги;\n"
        . "• ваши фотографии и описания;\n"
        . "• цены по сезонам;\n"
        . "• календарь свободных дат;\n"
        . "• онлайн-оплату, предоплату или заявку админу;\n"
        . "• Google Sheets или CRM;\n"
        . "• адрес, геометку и правила проживания;\n"
        . "• поддержку через Telegram, WhatsApp или звонок.";
}

function contactText(): string
{
    global $config;
    return '<b>Хотите такого бота для своей базы?</b>' . "\n\n"
        . 'Напишите мне в Telegram: @' . $config['contact_username'] . "\n\n"
        . "Для оценки проекта достаточно прислать:\n"
        . "1. список домиков и услуг;\n"
        . "2. цены;\n"
        . "3. фотографии;\n"
        . "4. правила проживания;\n"
        . "5. как сейчас принимаете бронирования.";
}

function guestGuide(string $country): string
{
    $info = countryInfo($country);
    return '<b>Информация для гостя после бронирования</b>' . "\n\n"
        . "<b>Как добраться</b>\n"
        . '• адрес: ' . $info['location'] . ";\n"
        . "• точную геометку можно отправить отдельной кнопкой;\n"
        . "• при въезде назовите имя, на которое оформлена бронь.\n\n"
        . "<b>Инструкция по заселению</b>\n"
        . "• заезд после 14:00;\n"
        . "• выезд до 12:00;\n"
        . "• администратор встретит вас или отправит инструкцию по ключам.\n\n"
        . "<b>Связь и поддержка</b>\n"
        . '• Telegram: ' . $info['support'] . "\n"
        . '• WhatsApp / телефон: ' . $info['phone'];
}

function showClientPath(int $chatId, array $state): void
{
    $country = $state['country'] ?? 'kz';
    $info = countryInfo($country);
    sendMessage(
        $chatId,
        "<b>Путь клиента: вымышленная база отдыха</b>\n\n"
        . "Сейчас вы увидите пример, как бот может выглядеть для гостя.\n"
        . "База отдыха вымышленная, а фотографии домиков и услуг сделаны с помощью ИИ.\n\n"
        . "<b>О нас:</b>\n" . $info['about'] . "\n\n"
        . "<b>Как забронировать:</b>\n"
        . "1. Нажмите «Выбрать даты».\n"
        . "2. Выберите заезд, выезд и домик.\n"
        . "3. Вернитесь в чат, чтобы увидеть сводку и следующий шаг.",
        mainKeyboard($country)
    );
}

function notifyOwner(array $from, string $action): void
{
    global $config;
    if (empty($config['admin_chat_id'])) {
        return;
    }
    $username = isset($from['username']) ? '@' . $from['username'] : 'без username';
    sendMessage(
        (int) $config['admin_chat_id'],
        "<b>Интерес к демо-боту</b>\n\n"
        . "Действие: {$action}\n"
        . 'Пользователь: ' . ($from['first_name'] ?? 'неизвестно') . "\n"
        . "Username: {$username}\n"
        . 'User ID: ' . ($from['id'] ?? 'неизвестно')
    );
}

function scheduleAutoStart(int $chatId, array $state): void
{
    global $config;
    $state['client_path_started'] = false;
    $state['auto_start_at'] = time() + (int) $config['auto_start_seconds'];
    saveState($chatId, $state);
}

if (defined('BOT_CRON') && BOT_CRON) {
    return;
}

$update = json_decode((string) file_get_contents('php://input'), true) ?: [];

if (isset($update['callback_query'])) {
    $query = $update['callback_query'];
    $chatId = (int) $query['message']['chat']['id'];
    $from = $query['from'];
    $data = $query['data'] ?? '';
    $state = loadState($chatId);

    if (strpos($data, 'country:') === 0) {
        $country = substr($data, 8);
        $state = ['country' => in_array($country, ['kz', 'ru'], true) ? $country : 'kz'];
        scheduleAutoStart($chatId, $state);
        sendMessage($chatId, 'Выбрано: ' . countryInfo($state['country'])['name']);
        sendMessage($chatId, ownerIntroText(), salesKeyboard());
    } elseif ($data === 'form:skip_phone') {
        $state['guest_phone'] = 'не указан';
        $state['form_step'] = 'guests';
        saveState($chatId, $state);
        sendMessage($chatId, 'Сколько гостей планируется? Например: 4');
    } elseif ($data === 'form:start') {
        $state['form_step'] = 'name';
        saveState($chatId, $state);
        sendMessage(
            $chatId,
            "<b>Оформим демо-заявку</b>\n\nВведите имя гостя. Можно написать вымышленное имя, это демонстрация."
        );
    } elseif ($data === 'form:skip_comment') {
        $state['guest_comment'] = 'нет комментария';
        $state['form_step'] = null;
        saveState($chatId, $state);
        finishForm($chatId, $state);
    } elseif ($data === 'pay:demo') {
        $country = $state['country'] ?? 'kz';
        $house = houses()[$state['house_code'] ?? 'house_4'] ?? houses()['house_4'];
        $nights = (int) ($state['nights'] ?? 1);
        $total = housePrices($country)[$state['house_code'] ?? 'house_4'] * $nights;
        sendMessage(
            $chatId,
            "<b>Бронь имитирована</b>\n\n"
            . 'Имя: ' . ($state['guest_name'] ?? 'не указано') . "\n"
            . 'Телефон: ' . ($state['guest_phone'] ?? 'не указан') . "\n"
            . 'Гостей: ' . ($state['guest_count'] ?? 'не указано') . "\n"
            . 'Комментарий: ' . ($state['guest_comment'] ?? 'нет комментария') . "\n\n"
            . 'Домик: ' . $house['title'] . "\n"
            . 'Заезд: ' . formatDateText($state['check_in'] ?? null) . "\n"
            . 'Выезд: ' . formatDateText($state['check_out'] ?? null) . "\n"
            . 'Сумма: <b>' . money($total, $country) . '</b>'
        );
        sendMessage($chatId, guestGuide($country), mainKeyboard($country));
        notifyOwner($from, 'нажал «Имитировать бронь»');
    } elseif ($data === 'support:open') {
        $country = $state['country'] ?? 'kz';
        $info = countryInfo($country);
        sendMessage($chatId, "<b>Поддержка</b>\n\nTelegram: {$info['support']}\nТелефон / WhatsApp: {$info['phone']}", mainKeyboard($country));
    }

    api('answerCallbackQuery', ['callback_query_id' => $query['id']]);
    exit;
}

if (!isset($update['message'])) {
    exit;
}

$message = $update['message'];
$chatId = (int) $message['chat']['id'];
$from = $message['from'] ?? [];
$text = trim((string) ($message['text'] ?? ''));
$state = loadState($chatId);

if (isset($message['web_app_data']['data'])) {
    $payload = json_decode($message['web_app_data']['data'], true) ?: [];
    $country = $payload['country'] ?? ($state['country'] ?? 'kz');
    $state = array_merge($state, [
        'country' => $country,
        'check_in' => $payload['check_in'] ?? null,
        'check_out' => $payload['check_out'] ?? null,
        'nights' => $payload['nights'] ?? 1,
        'house_code' => $payload['house_code'] ?? null,
        'client_path_started' => true,
    ]);
    saveState($chatId, $state);

    $house = houses()[$state['house_code']] ?? null;
    if (!$house) {
        sendMessage($chatId, 'Домик не выбран. Откройте календарь ещё раз и выберите домик.', mainKeyboard($country));
        exit;
    }

    $total = housePrices($country)[$state['house_code']] * (int) $state['nights'];
    sendMessage(
        $chatId,
        "<b>Отлично, выбор получен!</b>\n\n"
        . 'Домик: ' . $house['title'] . "\n"
        . 'Заезд: ' . formatDateText($state['check_in']) . "\n"
        . 'Выезд: ' . formatDateText($state['check_out']) . "\n"
        . 'Ночей: ' . $state['nights'] . "\n"
        . 'Итого: <b>' . money($total, $country) . "</b>\n\n"
        . 'Теперь оформим демо-заявку.',
        ['inline_keyboard' => [[['text' => 'Оформить заявку', 'callback_data' => 'form:start']]]]
    );
    exit;
}

if ($text === '/start' || strpos($text, '/start ') === 0) {
    $parts = explode(' ', $text, 2);
    if (isset($parts[1]) && in_array($parts[1], ['kz', 'ru'], true)) {
        $state = ['country' => $parts[1]];
        scheduleAutoStart($chatId, $state);
        sendMessage($chatId, ownerIntroText(), salesKeyboard());
    } else {
        saveState($chatId, []);
        sendMessage($chatId, '<b>Выберите страну</b>', countryKeyboard());
    }
    exit;
}

if ($text === '/book' || $text === 'Протестировать бота') {
    $state['client_path_started'] = true;
    saveState($chatId, $state);
    notifyOwner($from, $text === '/book' ? 'открыл бронирование через /book' : 'нажал «Протестировать бота»');
    showClientPath($chatId, $state);
    exit;
}

if ($text === '/support' || $text === 'Связаться') {
    notifyOwner($from, 'нажал «Связаться»');
    sendMessage($chatId, contactText(), salesKeyboard());
    exit;
}

if ($text === 'Сменить страну') {
    sendMessage($chatId, '<b>Выберите страну</b>', countryKeyboard());
    exit;
}

if ($text === 'Что решает бот') {
    sendMessage($chatId, benefitsText(), salesKeyboard());
    exit;
}

if ($text === 'Что можно настроить') {
    sendMessage($chatId, customizationText(), salesKeyboard());
    exit;
}

if ($text === 'Пример заявки админу') {
    $country = $state['country'] ?? 'kz';
    sendMessage($chatId, "<b>Пример заявки админу</b>\n\nДомик: Family на 4 человека\nДаты: 12.07 - 14.07\nГостей: 4\nСумма: " . money(housePrices($country)['house_4'] * 2, $country) . "\nСтатус: ожидает подтверждения", salesKeyboard());
    exit;
}

if ($text === 'Цены') {
    $country = $state['country'] ?? 'kz';
    $prices = housePrices($country);
    sendMessage($chatId, "<b>Цены демо-версии</b>\n\n• Домик на 2 человека — " . money($prices['house_2'], $country) . " / сутки\n• Домик на 4 человека — " . money($prices['house_4'], $country) . " / сутки\n• Домик на 6 человек — " . money($prices['house_6'], $country) . ' / сутки', mainKeyboard($country));
    exit;
}

if ($text === 'Адрес') {
    $country = $state['country'] ?? 'kz';
    sendMessage($chatId, '<b>Адрес базы отдыха:</b>' . "\n" . countryInfo($country)['location'], mainKeyboard($country));
    exit;
}

if ($text === 'Контакты') {
    $country = $state['country'] ?? 'kz';
    $info = countryInfo($country);
    sendMessage($chatId, "<b>Контакты</b>\n\nTelegram: {$info['support']}\nТелефон / WhatsApp: {$info['phone']}", mainKeyboard($country));
    exit;
}

if ($text === 'Что есть на территории') {
    sendMessage($chatId, "На территории есть домики, беседки, баня, бассейн, мангальная зона, парковка и прогулочная зона.", mainKeyboard($state['country'] ?? 'kz'));
    exit;
}

if ($text === 'Условия проживания') {
    sendMessage($chatId, "Условия проживания:\n\n• заезд после 14:00\n• выезд до 12:00\n• бронь подтверждается после предоплаты или администратором\n• с животными — по согласованию", mainKeyboard($state['country'] ?? 'kz'));
    exit;
}

if ($text === 'Информация для гостя') {
    sendMessage($chatId, guestGuide($state['country'] ?? 'kz'), mainKeyboard($state['country'] ?? 'kz'));
    exit;
}

if (($state['form_step'] ?? null) === 'name') {
    $state['guest_name'] = $text ?: 'Гость';
    $state['form_step'] = 'phone';
    saveState($chatId, $state);
    sendMessage($chatId, 'Введите номер телефона или нажмите «Пропустить». Для демо можно не оставлять настоящий номер.', ['inline_keyboard' => [[['text' => 'Пропустить', 'callback_data' => 'form:skip_phone']]]]);
    exit;
}

if (($state['form_step'] ?? null) === 'phone') {
    $state['guest_phone'] = $text ?: 'не указан';
    $state['form_step'] = 'guests';
    saveState($chatId, $state);
    sendMessage($chatId, 'Сколько гостей планируется? Например: 4');
    exit;
}

if (($state['form_step'] ?? null) === 'guests') {
    $state['guest_count'] = $text ?: 'не указано';
    $state['form_step'] = 'comment';
    saveState($chatId, $state);
    sendMessage($chatId, 'Есть комментарий к бронированию? Можно нажать «Пропустить».', ['inline_keyboard' => [[['text' => 'Пропустить', 'callback_data' => 'form:skip_comment']]]]);
    exit;
}

if (($state['form_step'] ?? null) === 'comment') {
    $state['guest_comment'] = $text ?: 'нет комментария';
    $state['form_step'] = null;
    saveState($chatId, $state);
    finishForm($chatId, $state);
    exit;
}

sendMessage($chatId, 'Выберите действие в меню.', salesKeyboard());

function finishForm(int $chatId, array $state): void
{
    $country = $state['country'] ?? 'kz';
    $house = houses()[$state['house_code'] ?? 'house_4'] ?? houses()['house_4'];
    $nights = (int) ($state['nights'] ?? 1);
    $total = housePrices($country)[$state['house_code'] ?? 'house_4'] * $nights;
    saveState($chatId, $state);
    sendMessage(
        $chatId,
        "<b>Демо-заявка сформирована</b>\n\n"
        . 'Имя: ' . ($state['guest_name'] ?? 'не указано') . "\n"
        . 'Телефон: ' . ($state['guest_phone'] ?? 'не указан') . "\n"
        . 'Гостей: ' . ($state['guest_count'] ?? 'не указано') . "\n"
        . 'Комментарий: ' . ($state['guest_comment'] ?? 'нет комментария') . "\n\n"
        . 'Домик: ' . $house['title'] . "\n"
        . 'Заезд: ' . formatDateText($state['check_in'] ?? null) . "\n"
        . 'Выезд: ' . formatDateText($state['check_out'] ?? null) . "\n"
        . 'Сумма: <b>' . money($total, $country) . '</b>',
        finalBookingKeyboard()
    );
}
