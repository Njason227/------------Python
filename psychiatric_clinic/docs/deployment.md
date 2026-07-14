# Развёртывание приложения на веб-сервере

## Содержание
1. [Подготовка среды](#1-подготовка-среды)
2. [Настройка PostgreSQL](#2-настройка-postgresql)
3. [Развёртывание Django-приложения](#3-развёртывание-django-приложения)
4. [Первичная инициализация и проверка](#4-первичная-инициализация-и-проверка)
5. [Настройка Gunicorn](#5-настройка-gunicorn)
6. [Настройка Nginx](#6-настройка-nginx)
7. [Настройка Apache (альтернатива)](#7-настройка-apache-альтернатива)
8. [Настройка системного сервиса (systemd / supervisor)](#8-настройка-системного-сервиса-systemd--supervisor)
9. [SSL-сертификат (Let's Encrypt)](#9-ssl-сертификат-lets-encrypt)
10. [Полная проверка запуска](#10-полная-проверка-запуска)
11. [Управление сервисами и обслуживание](#11-управление-сервисами-и-обслуживание)
12. [Автозапуск при перезагрузке сервера](#12-автозапуск-при-перезагрузке-сервера)

---

## 1. Подготовка среды

### Требования
- Ubuntu 22.04/24.04 LTS (или Debian 12)
- Python 3.12+
- PostgreSQL 16+
- Nginx или Apache 2.4+
- root-доступ

### Установка пакетов системы

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    libpq-dev gcc nginx supervisor
```

---

## 2. Настройка PostgreSQL

```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### Создание БД и пользователя

```bash
sudo -u postgres psql
```

```sql
CREATE USER psych_user WITH PASSWORD 'ВАШ_СТОЙКИЙ_ПАРОЛЬ';
CREATE DATABASE psych_db OWNER psych_user;
ALTER USER psych_user CREATEDB;
\q
```

---

## 3. Развёртывание Django-приложения

### Копирование проекта на сервер

```bash
# Скопировать проект на сервер (например, через scp/rsync)
scp -r psychiatric_clinic/ user@server:/opt/psychiatric_clinic

# Или клонировать из репозитория
sudo mkdir -p /opt/psychiatric_clinic
sudo chown $USER:$USER /opt/psychiatric_clinic
```

### Создание виртуального окружения

```bash
cd /opt/psychiatric_clinic
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### Настройка переменных окружения

Создайте файл `/opt/psychiatric_clinic/.env`:

```env
DJANGO_SECRET_KEY=сгенерируйте-случайный-ключ-минимум-50-символов
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=ваш-домен.ru,www.ваш-домен.ru
DATABASE_URL=psycopg2://psych_user:ПАРОЛЬ@localhost:5432/psych_db
```

Генерация секретного ключа:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Настройка settings.py

Убедитесь, что `config/settings.py` поддерживает чтение из `.env`. Добавьте в начало файла:

```python
import os
from pathlib import Path

# ... существующий код ...

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-...')
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'psych_db'),
        'USER': os.environ.get('DB_USER', 'psych_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

---

## 4. Первичная инициализация и проверка

### 4.1. Предварительная проверка импортов

```bash
cd /opt/psychiatric_clinic
source venv/bin/activate

# Проверка импортов (не должно быть ошибок)
python -c "import django; django.setup(); print('Django OK')"

# Проверка подключения к БД
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT 1')
print('PostgreSQL OK')
"
```

### 4.2. Первичная инициализация базы данных

```bash
cd /opt/psychiatric_clinic
source venv/bin/activate

# Применение миграций
python manage.py migrate

# Загрузка начальных данных (справочники МКБ-11, отделения)
python manage.py load_initial_data

# Создание суперпользователя (запомните логин и пароль!)
python manage.py createsuperuser
# Введите: username, email (можно пустой), password дважды

# Создание тестового врача (опционально)
python manage.py shell -c "
from apps.accounts.models import User
User.objects.create_user(
    'doctor', 'doctor@clinic.ru', 'doctor123',
    role='doctor', first_name='Иван', last_name='Петров'
)
print('Тестовый врач создан: doctor / doctor123')
"

# Сбор статических файлов
python manage.py collectstatic --noinput
```

### 4.3. Проверка через встроенный сервер

Запустите Django-встроенный сервер для финальной проверки перед продакшн-запуском:

```bash
cd /opt/psychiatric_clinic
source venv/bin/activate
python manage.py runserver 0.0.0.0:8080
```

Откройте в браузере `http://IP_СЕРВЕРА:8080` и проверьте:
- [ ] Отображается страница входа
- [ ] Вход под учётной записью admin работает
- [ ] Справочники загружены (35 диагнозов МКБ-11, 7 отделений)
- [ ] Можно зарегистрировать пациента
- [ ] Авто-распределение работает
- [ ] Панель статистики отображается

Остановите сервер: `Ctrl+C`.

---

## 5. Настройка Gunicorn

### Конфигурация Gunicorn

Создайте `/opt/psychiatric_clinic/gunicorn_config.py`:

```python
import multiprocessing

bind = '127.0.0.1:8000'
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
timeout = 120
max_requests = 2000
max_requests_jitter = 200
keepalive = 5
errorlog = '/var/log/gunicorn/error.log'
accesslog = '/var/log/gunicorn/access.log'
loglevel = 'info'
proc_name = 'psychiatric_clinic'
preload_app = True
user = 'www-data'
group = 'www-data'
backlog = 2048
```

```bash
sudo mkdir -p /var/log/gunicorn
sudo chown www-data:www-data /var/log/gunicorn
```

### Тестовый запуск Gunicorn

```bash
cd /opt/psychiatric_clinic
source venv/bin/activate

gunicorn config.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log \
    --log-level info

# Проверка в другом терминале:
curl -I http://127.0.0.1:8000/

# Остановка: Ctrl+C
```

---

## 6. Настройка Nginx

### Установка

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
```

### Конфигурация сервера

Создайте `/etc/nginx/sites-available/psychiatric_clinic`:

```nginx
upstream django_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name ваш-домен.ru www.ваш-домен.ru;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ваш-домен.ru www.ваш-домен.ru;

    # SSL (раскомментировать после настройки Let's Encrypt — раздел 9)
    # ssl_certificate /etc/letsencrypt/live/ваш-домен.ru/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/ваш-домен.ru/privkey.pem;

    charset utf-8;
    client_max_body_size 10M;

    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 120s;

    access_log /var/log/nginx/psychiatric_access.log;
    error_log /var/log/nginx/psychiatric_error.log;

    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_proxied any;
    gzip_comp_level 5;
    gzip_types text/plain text/css text/xml application/json
               application/javascript application/xml+rss image/svg+xml;

    location /static/ {
        alias /opt/psychiatric_clinic/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /opt/psychiatric_clinic/media/;
        expires 7d;
    }

    location /favicon.ico {
        alias /opt/psychiatric_clinic/staticfiles/admin/img/favicon.ico;
        log_not_found off;
        access_log off;
    }

    location / {
        proxy_pass http://django_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

### Активация конфигурации

```bash
sudo ln -s /etc/nginx/sites-available/psychiatric_clinic /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

---

## 7. Настройка Apache (альтернатива)

### Установка

```bash
sudo apt install -y apache2 libapache2-mod-proxy-proxy-uwsgi libapache2-mod-wsgi-py3
sudo systemctl enable apache2
```

### Конфигурация virtual host

Создайте `/etc/apache2/sites-available/psychiatric_clinic.conf`:

```apache
<VirtualHost *:80>
    ServerName ваш-домен.ru
    ServerAlias www.ваш-домен.ru
    Redirect permanent / https://ваш-домен.ru/
</VirtualHost>

<VirtualHost *:443>
    ServerName ваш-домен.ru
    ServerAlias www.ваш-домен.ru

    # SSL (раскомментировать после настройки Let's Encrypt — раздел 9)
    # SSLEngine on
    # SSLCertificateFile /etc/letsencrypt/live/ваш-домен.ru/fullchain.pem
    # SSLCertificateKeyFile /etc/letsencrypt/live/ваш-домен.ru/privkey.pem

    DocumentRoot /opt/psychiatric_clinic

    ErrorLog ${APACHE_LOG_DIR}/psychiatric_error.log
    CustomLog ${APACHE_LOG_DIR}/psychiatric_access.log combined

    Alias /static/ /opt/psychiatric_clinic/staticfiles/
    <Directory /opt/psychiatric_clinic/staticfiles/>
        Require all granted
    </Directory>

    Alias /media/ /opt/psychiatric_clinic/media/
    <Directory /opt/psychiatric_clinic/media/>
        Require all granted
    </Directory>

    WSGIDaemonProcess psychiatric python-path=/opt/psychiatric_clinic python-home=/opt/psychiatric_clinic/venv
    WSGIProcessGroup psychiatric
    WSGIScriptAlias / /opt/psychiatric_clinic/config/wsgi.py

    <Directory /opt/psychiatric_clinic/config/>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    <DirectoryMatch /\.>
        Require all denied
    </DirectoryMatch>
</VirtualHost>
```

### Активация

```bash
sudo a2enmod ssl proxy proxy_http headers rewrite wsgi
sudo a2ensite psychiatric_clinic
sudo a2dissite 000-default.conf
sudo apache2ctl configtest
sudo systemctl reload apache2
```

---

## 8. Настройка системного сервиса (systemd / supervisor)

### Вариант A: systemd (рекомендуется)

#### 8.1. Создание systemd-сокета

Создайте файл `/etc/systemd/system/gunicorn.socket`:

```ini
[Unit]
Description=Gunicorn socket for Psychiatric Clinic

[Socket]
ListenStream=/run/gunicorn.sock
SocketUser=www-data

[Install]
WantedBy=sockets.target
```

#### 8.2. Создание systemd-сервиса

Создайте файл `/etc/systemd/system/gunicorn.service`:

```ini
[Unit]
Description=Gunicorn daemon for Psychiatric Clinic
Requires=gunicorn.socket
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/psychiatric_clinic

EnvironmentFile=/opt/psychiatric_clinic/.env

ExecStart=/opt/psychiatric_clinic/venv/bin/gunicorn \
    config.wsgi:application \
    --bind unix:/run/gunicorn.sock \
    --workers 3 \
    --worker-class sync \
    --timeout 120 \
    --max-requests 2000 \
    --max-requests-jitter 200 \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log \
    --log-level info \
    --proc-name psychiatric_clinic \
    --preload-app

Restart=on-failure
RestartSec=5
TimeoutStopSec=30

LimitNOFILE=65535
ProtectSystem=full
PrivateTmp=true

StandardOutput=journal
StandardError=journal
SyslogIdentifier=psychiatric_clinic

[Install]
WantedBy=multi-user.target
```

#### 8.3. Активация и запуск

```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска при старте сервера
sudo systemctl enable gunicorn.socket
sudo systemctl enable gunicorn.service

# Запуск
sudo systemctl start gunicorn.socket
sudo systemctl start gunicorn.service

# Проверка статуса
sudo systemctl status gunicorn.socket
sudo systemctl status gunicorn.service

# Проверка что сокет-файл создан и доступен
ls -la /run/gunicorn.sock
# Ожидаемый вывод: srwxrwxrwx 1 www-data www-data ... /run/gunicorn.sock

# Проверка ответа через сокет
curl -I http://127.0.0.1:8000/
# Ожидаемый вывод: HTTP/1.1 200 OK
```

#### 8.4. Диагностика проблем systemd

```bash
# Полный лог сервиса
sudo journalctl -u gunicorn.service --no-pager -n 50

# Логи при аварийном завершении
sudo journalctl -u gunicorn.service -p err --no-pager

# Проверка переменных окружения
sudo systemctl show gunicorn.service -p Environment

# Проверка прав на файлы
ls -la /opt/psychiatric_clinic/
ls -la /var/log/gunicorn/

# Проверка что БД доступна из под www-data
sudo -u www-data /opt/psychiatric_clinic/venv/bin/python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.db import connection; connection.ensure_connection()
print('DB OK')
"
```

### Вариант B: supervisor (альтернатива)

Создайте `/etc/supervisor/conf.d/psychiatric_clinic.conf`:

```ini
[program:psychiatric_clinic]
command=/opt/psychiatric_clinic/venv/bin/gunicorn config.wsgi:application -c /opt/psychiatric_clinic/gunicorn_config.py
directory=/opt/psychiatric_clinic
user=www-data
autostart=true
autorestart=true
startretries=3
startsecs=5
redirect_stderr=true
stdout_logfile=/var/log/gunicorn/supervisor.log
stderr_logfile=/var/log/gunicorn/supervisor_error.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
stopwaitsecs=30
stopasgroup=true
killasgroup=true
environment=
    DJANGO_SECRET_KEY="ваш-ключ",
    DJANGO_DEBUG="False",
    DJANGO_ALLOWED_HOSTS="ваш-домен.ru",
    DB_NAME="psych_db",
    DB_USER="psych_user",
    DB_PASSWORD="пароль"
```

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start psychiatric_clinic
sudo supervisorctl status psychiatric_clinic
```

---

## 9. SSL-сертификат (Let's Encrypt)

```bash
sudo apt install -y certbot

# Для Nginx:
sudo certbot --nginx -d ваш-домен.ru -d www.ваш-домен.ru

# Для Apache:
sudo certbot --apache -d ваш-домен.ru -d www.ваш-домен.ru

# Автообновление (certbot создаёт таймер автоматически)
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Проверка таймера
sudo systemctl status certbot.timer

# Ручная проверка обновления
sudo certbot renew --dry-run
```

---

## 10. Полная проверка запуска

### 10.1. Последовательная проверка каждого сервиса

Выполняйте команды по порядку. Каждый шаг должен завершаться без ошибок:

```bash
echo "=== Шаг 1: PostgreSQL ==="
sudo systemctl status postgresql --no-pager
sudo -u postgres psql -c "SELECT 1 AS connection_test;" psych_db

echo ""
echo "=== Шаг 2: Gunicorn (процесс) ==="
ps aux | grep gunicorn | grep -v grep
# Должен показать master + 3 worker-процесса

echo ""
echo "=== Шаг 3: Gunicorn (сокет) ==="
ls -la /run/gunicorn.sock
# Файл должен существовать и быть доступен для www-data

echo ""
echo "=== Шаг 4: Gunicorn (ответ) ==="
curl -sI http://127.0.0.1:8000/ | head -5
# Должен вернуть HTTP/1.1 200 OK

echo ""
echo "=== Шаг 5: Nginx ==="
sudo systemctl status nginx --no-pager
sudo nginx -t
# Оба теста: "syntax is ok" / "test is successful"

echo ""
echo "=== Шаг 6: Nginx (ответ) ==="
curl -sI https://ваш-домен.ru/ | head -10
# Должен вернуть HTTP/2 200

echo ""
echo "=== Шаг 7: Статика ==="
curl -sI https://ваш-домен.ru/static/css/style.css | head -5
# Должен вернуть 200 с Content-Type: text/css

echo ""
echo "=== Шаг 8: Логи ==="
echo "--- Gunicorn ---"
tail -3 /var/log/gunicorn/access.log 2>/dev/null || echo "Лог-файл не найден"
echo "--- Nginx ---"
sudo tail -3 /var/log/nginx/psychiatric_access.log 2>/dev/null || echo "Лог-файл не найден"
```

### 10.2. Проверка через браузер

Откройте `https://ваш-домен.ru` и проверьте:

| Проверка | Ожидаемый результат |
|---|---|
| Главная страница | Отображается карточка «Войти в систему» |
| Вход (admin) | Перенаправление на панель управления |
| Панель статистики | Показывает 0 пациентов, 7 отделений |
| Справочники | Диагнозы МКБ-11 загружены (35 шт.) |
| Регистрация пациента | Форма создания, корректная работа полей |
| Авто-распределение | Пациент получает статус «Распределён» |
| Админ-панель `/admin/` | Доступна, вход работает |

### 10.3. Проверка извне (с другого компьютера)

```bash
# С домашнего компьютера:
curl -I https://ваш-домен.ru/

# Проверка портов
nmap -p 80,443 ваш-домен.ru

# Проверка SSL-сертификата
openssl s_client -connect ваш-домен.ru:443 -servername ваш-домен.ru < /dev/null 2>/dev/null | openssl x509 -noout -dates
```

---

## 11. Управление сервисами и обслуживание

### Команды systemctl

```bash
# Статус всех сервисов
sudo systemctl status gunicorn.socket gunicorn.service nginx postgresql

# Перезапуск всех
sudo systemctl restart gunicorn.socket gunicorn.service nginx

# Остановка всех
sudo systemctl stop gunicorn.service gunicorn.socket nginx

# Запуск всех
sudo systemctl start nginx gunicorn.socket gunicorn.service
```

### Просмотр логов

```bash
# Логи Gunicorn (через journalctl)
sudo journalctl -u gunicorn.service -f              # в реальном времени
sudo journalctl -u gunicorn.service --since today     # за сегодня
sudo journalctl -u gunicorn.service -n 100            # последние 100 строк

# Логи Nginx
sudo tail -f /var/log/nginx/psychiatric_access.log
sudo tail -f /var/log/nginx/psychiatric_error.log

# Логи Gunicorn (файловые)
sudo tail -f /var/log/gunicorn/access.log
sudo tail -f /var/log/gunicorn/error.log

# Логи PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-16-main.log

# Все ошибки Django
sudo journalctl -u gunicorn.service | grep -i "error\|traceback\|exception"
```

### Перезапуск после изменений в коде

```bash
cd /opt/psychiatric_clinic
source venv/bin/activate

# 1. Обновить код
git pull

# 2. Применить новые миграции (если есть)
python manage.py migrate

# 3. Пересобрать статику
python manage.py collectstatic --noinput

# 4. Перезапустить Gunicorn
sudo systemctl restart gunicorn.service

# 5. Проверить
sudo systemctl status gunicorn.service
curl -sI http://127.0.0.1:8000/ | head -3
```

### Обновление зависимостей

```bash
cd /opt/psychiatric_clinic
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart gunicorn.service
```

### Резервное копирование БД

```bash
# Ручной бэкап
sudo mkdir -p /backup
pg_dump -U psych_user psych_db > /backup/psych_db_$(date +%Y%m%d_%H%M%S).sql

# Автоматический бэкап каждый день в 2:00 (добавить в crontab)
echo "0 2 * * * pg_dump -U psych_user psych_db | gzip > /backup/psych_db_\$(date +\%Y\%m\%d).sql.gz" | sudo tee -a /var/spool/cron/crontabs/root

# Восстановление из бэкапа
psql -U psych_user psych_db < /backup/psych_db_20260712.sql
```

### Мониторинг

```bash
# Использование ресурсов
htop

# Загрузка сервера
uptime

# Использование диска
df -h

# Размер логов
du -sh /var/log/gunicorn/ /var/log/nginx/ /var/log/postgresql/

# Очистка старых логов (старше 30 дней)
sudo find /var/log/gunicorn/ -name "*.log" -mtime +30 -delete
sudo find /var/log/nginx/ -name "*.log" -mtime +30 -delete

# Проверка соединений с БД
sudo -u postgres psql -c "SELECT count(*) AS active_connections FROM pg_stat_activity;" psych_db
```

---

## 12. Автозапуск при перезагрузке сервера

```bash
# Убедитесь что все сервисы включены в автозапуск
sudo systemctl is-enabled postgresql
sudo systemctl is-enabled nginx
sudo systemctl is-enabled gunicorn.socket
sudo systemctl is-enabled gunicorn.service

# Если какой-то не включён:
sudo systemctl enable <имя_сервиса>
```

После перезагрузки сервера все сервисы стартуют автоматически.

---

## Полезные команды (шпаргалка)

```bash
# Перезапуск всех сервисов
sudo systemctl restart gunicorn.socket gunicorn.service nginx postgresql

# Просмотр ошибок
sudo journalctl -u gunicorn.service -f
sudo journalctl -u nginx -f

# Обновление приложения
cd /opt/psychiatric_clinic
source venv/bin/activate
git pull
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn.service

# Проверка конфигурации Nginx
sudo nginx -t

# Проверка конфигурации Apache
sudo apache2ctl configtest

# Проверка статуса всех сервисов
systemctl status postgresql nginx gunicorn.socket gunicorn.service
```
