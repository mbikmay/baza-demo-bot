# Перенос Telegram-бота на сервер

Мини-апп может оставаться на обычном хостинге `cp.sweb.ru`, потому что это статические файлы:

```text
webapp/index.html
webapp/styles.css
webapp/script.js
webapp/photos_optimized/
```

Но сам Telegram-бот на Python должен работать постоянно. Для этого нужен сервер/VPS/VDS, где можно запустить постоянный процесс.

## Важно

Если у вас на SpaceWeb только обычный виртуальный хостинг для сайта, он может не подойти для Telegram-бота на polling, потому что бот должен быть постоянно запущен.

Лучшие варианты:

```text
1. VPS/VDS на SpaceWeb
2. Timeweb Cloud
3. Selectel
4. Beget VPS
5. любой Ubuntu VPS
```

Мини-апп при этом можно оставить на текущем хостинге.

## Что загрузить на сервер

На сервер нужно загрузить:

```text
demo_bot.py
requirements.txt
webapp/photos_optimized/
```

Папка `webapp` целиком нужна боту только для отправки фотографий. Сам мини-апп может продолжать лежать на вашем сайте.

## Команды для Ubuntu-сервера

Подключиться к серверу:

```bash
ssh root@SERVER_IP
```

Обновить систему:

```bash
apt update && apt upgrade -y
```

Установить Python:

```bash
apt install -y python3 python3-venv python3-pip
```

Создать папку проекта:

```bash
mkdir -p /opt/baza-bot
cd /opt/baza-bot
```

Загрузить файлы проекта в `/opt/baza-bot`.

Создать виртуальное окружение:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Создать файл переменных:

```bash
nano /opt/baza-bot/.env
```

Вставить:

```text
BOT_TOKEN=токен_от_BotFather
WEBAPP_URL=https://ссылка-на-mini-app
ADMIN_CHAT_ID=846207345
```

## Проверочный запуск

```bash
cd /opt/baza-bot
source .venv/bin/activate
set -a
source .env
set +a
python demo_bot.py
```

Если бот отвечает в Telegram, остановить его:

```text
Ctrl + C
```

## Запуск как постоянной службы

Создать systemd service:

```bash
nano /etc/systemd/system/baza-bot.service
```

Вставить:

```ini
[Unit]
Description=Baza Telegram Demo Bot
After=network.target

[Service]
WorkingDirectory=/opt/baza-bot
EnvironmentFile=/opt/baza-bot/.env
ExecStart=/opt/baza-bot/.venv/bin/python /opt/baza-bot/demo_bot.py
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
```

Запустить:

```bash
systemctl daemon-reload
systemctl enable baza-bot
systemctl start baza-bot
```

Проверить статус:

```bash
systemctl status baza-bot
```

Смотреть логи:

```bash
journalctl -u baza-bot -f
```

## Обновление бота

После изменения файлов:

```bash
systemctl restart baza-bot
```

## Что делать с мини-аппом

Мини-апп загрузить на сайт:

```text
index.html
styles.css
script.js
photos_optimized/
```

Ссылка на него должна быть HTTPS. Эту ссылку указать в `WEBAPP_URL`.

Например:

```text
WEBAPP_URL=https://example.ru/baza-demo/
```

