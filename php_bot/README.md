# PHP webhook версия бота

Эта версия нужна, если хочется разместить Telegram-бота на обычном PHP-хостинге без VPS.

## Файлы

```text
php_bot/bot.php
php_bot/cron_autostart.php
php_bot/config.example.php
php_bot/storage/
```

## Установка

1. Скопируйте `config.example.php` в `config.php`.
2. Вставьте токен бота и ссылку на календарь:

```php
'bot_token' => 'TOKEN_FROM_BOTFATHER',
'webhook_url' => 'https://ваш-сайт.ru/php_bot/bot.php',
'webapp_url' => 'https://ваш-сайт.ru/webapp/',
'admin_chat_id' => '846207345',
```

3. Загрузите папку `php_bot` на хостинг.
4. Проверьте, что папка `php_bot/storage/users` доступна для записи.

## Webhook и синее меню

Откройте в браузере:

```text
https://ваш-сайт.ru/php_bot/setup.php
```

Этот файл установит webhook и команды синего меню:

```text
/start
/book
/support
```

## Проверка если бот не работает

Откройте в браузере:

```text
https://ваш-сайт.ru/php_bot/health.php
```

Там должно быть:

```text
config.php: OK
cURL: OK
storage/users writable: OK
bot_token: OK
```

Если бот всё равно не отвечает, проверьте файл:

```text
php_bot/storage/error.log
```

## Автостарт через 5 минут

На обычном PHP-хостинге фоновых процессов нет, поэтому автостарт делается через cron.

Создайте cron-задачу раз в минуту:

```bash
php /path/to/site/php_bot/cron_autostart.php
```

Если в панели хостинга нельзя указать `php`, можно открыть cron по URL, если хостинг это поддерживает:

```text
https://ваш-сайт.ru/php_bot/cron_autostart.php
```

Лучше защитить cron-файл секретным параметром, если будете открывать его по URL.
