# 📋 **РУКОВОДСТВО ПОЛЬЗОВАТЕЛЯ**
## Система автоматизированной обработки Excel-файлов

**Версия:** 1.0
**Дата:** 30 января 2025 г.
**Автор:** Система разработана для автоматизации обработки отчетности

---

## 📖 **СОДЕРЖАНИЕ**

1. [Введение и обзор системы](#введение-и-обзор-системы)
2. [Архитектура и компоненты](#архитектура-и-компоненты)
3. [Установка и настройка](#установка-и-настройка)
4. [Конфигурирование системы](#конфигурирование-системы)
5. [Запуск и управление](#запуск-и-управление)
6. [Мониторинг и диагностика](#мониторинг-и-диагностика)
7. [Обработка ошибок](#обработка-ошибок)
8. [API документация](#api-документация)
9. [Безопасность и производительность](#безопасность-и-производительность)
10. [Устранение неполадок](#устранение-неполадок)
11. [Часто задаваемые вопросы](#часто-задаваемые-вопросы)

---

## 📚 **ВВЕДЕНИЕ И ОБЗОР СИСТЕМЫ**

### Назначение системы

Система автоматизированной обработки Excel-файлов предназначена для:

- 📧 **Автоматического мониторинга** почтовых ящиков на наличие новых сообщений с Excel-вложениями
- 📊 **Конвертации** .xlsx файлов в .csv формат с заданными параметрами
- 🔄 **Передачи** обработанных файлов на SFTP-сервер
- 📈 **Мониторинга** всех операций с детальным логгированием
- 🛡️ **Обеспечения** надежности и безопасности обработки данных

### Ключевые преимущества

✅ **Полная автоматизация** - система работает 24/7 без вмешательства пользователя
✅ **Высокая надежность** - встроенная система обработки ошибок и повторных попыток
✅ **Enterprise-level безопасность** - защита от DDoS, валидация файлов, логгирование
✅ **Масштабируемость** - готовность к production deployment
✅ **Полная отслеживаемость** - детальные логи и метрики для мониторинга

### Архитектурная схема

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   📧 Email      │ ──▶│  🔄 Processing  │ ──▶│  📤 SFTP       │
│   Server        │    │   Engine        │    │   Upload       │
│                 │    │                 │    │                 │
│ • IMAP/POP3     │    │ • File          │    │ • Validation    │
│ • Filtering     │    │   Conversion    │    │ • Hash Check    │
│ • Deduplication │    │ • Hash          │    │ • Retry Logic   │
└─────────────────┘    │   Calculation   │    └─────────────────┘
                       │ • Database      │
                       │   Logging       │
                       └─────────────────┘
                               │
                       ┌─────────────────┐
                       │  📊 Monitoring  │
                       │                 │
                       │ • Health Checks │
                       │ • Metrics       │
                       │ • Alerting      │
                       │ • Rate Limiting │
                       └─────────────────┘
```

---

## 🏗️ **АРХИТЕКТУРА И КОМПОНЕНТЫ**

### Основные компоненты системы

#### 1. **Email Processing Module** 📧
- **Назначение:** Мониторинг почтовых ящиков и извлечение вложений
- **Функции:**
  - Подключение к IMAP/POP3 серверам
  - Фильтрация по whitelist отправителей
  - Дедупликация по Message-ID
  - Обработка только .xlsx вложений
- **Интервал:** Каждый час (настраивается)

#### 2. **File Processing Engine** 🔄
- **Назначение:** Конвертация и обработка файлов
- **Функции:**
  - Конвертация .xlsx → .csv (UTF-8 with BOM)
  - Вычисление хеш-сумм (SHA256)
  - Сохранение в структурированной папочной системе
  - Валидация целостности файлов
- **Выходной формат:** `RS_stoplist_{YYYYMMDD}.csv`

#### 3. **SFTP Upload Service** 📤
- **Назначение:** Безопасная передача файлов
- **Функции:**
  - Key-based аутентификация
  - Проверка целостности после загрузки
  - Retry логика с exponential backoff
  - Автоматическое удаление поврежденных файлов

#### 4. **Database Layer** 🗄️
- **СУБД:** PostgreSQL 15+
- **Таблицы:**
  - `processed_files` - учет обработанных файлов
  - `operation_logs` - логи всех операций
- **Функции:** ACID-совместимость, индексирование, backup

#### 5. **Monitoring & Alerting** 📊
- **Health Checks:** Проверка состояния всех зависимостей
- **Metrics:** Prometheus-совместимые метрики
- **Notifications:** Email + Telegram уведомления
- **Rate Limiting:** Защита от DDoS атак

#### 6. **Security Layer** 🛡️
- **Circuit Breaker:** Защита от каскадных сбоев
- **Error Categorization:** CRITICAL/RECOVERABLE/WARNING
- **Graceful Degradation:** 4 уровня деградации сервиса
- **Authentication:** Key-based доступ к SFTP

---

## 🚀 **УСТАНОВКА И НАСТРОЙКА**

### Системные требования

#### Минимальные требования:
- **ОС:** Linux (Ubuntu 20.04+), macOS, Windows 10+
- **RAM:** 2 GB
- **CPU:** 2 cores
- **Диск:** 10 GB свободного места
- **Docker:** 20.10+
- **Docker Compose:** 2.0+

#### Рекомендуемые требования (Production):
- **ОС:** Ubuntu 22.04 LTS или CentOS 8+
- **RAM:** 8 GB
- **CPU:** 4 cores
- **Диск:** 50 GB SSD
- **Сеть:** Стабильное интернет-соединение
- **Backup:** Регулярное резервное копирование

### Пошаговая установка

#### Шаг 1: Подготовка окружения

```bash
# 1. Клонирование репозитория
git clone https://github.com/your-org/rs-stoplist-project.git
cd rs-stoplist-project

# 2. Проверка Docker
docker --version
docker-compose --version

# 3. Создание директорий
mkdir -p storage/sftp_upload
mkdir -p logs
mkdir -p data/postgres
```

#### Шаг 2: Настройка SSH ключей

```bash
# 1. Генерация SSH ключей для SFTP (если нужно)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/sftp_key -N ""

# 2. Проверка существующих ключей
ls -la ~/.ssh/

# 3. Копирование ключей в проект (для development)
cp ~/.ssh/id_rsa ~/.ssh/sftp_key  # приватный ключ
cp ~/.ssh/id_rsa.pub ~/.ssh/sftp_key.pub  # публичный ключ
```

#### Шаг 3: Настройка переменных окружения

Создайте файл `.env` в корневой директории:

```bash
# Создание .env файла
cp .env.example .env  # если есть шаблон
# или создать вручную:
touch .env
```

**Содержимое .env файла:**

```bash
# =====================================
# Database Configuration
# =====================================
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_USER=emailprocessor
POSTGRES_PASSWORD=secure_password_123
POSTGRES_DB=email_processor_db

# =====================================
# Email Configuration
# =====================================
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-specific-password

# =====================================
# SFTP Configuration
# =====================================
SFTP_HOST=sftp
SFTP_USER=sftpuser
SFTP_PASS=pass

# =====================================
# Notifications
# =====================================
TG_BOT_TOKEN=your-telegram-bot-token
TG_CHAT_ID=your-telegram-chat-id

# =====================================
# Security & Performance
# =====================================
SECRET_KEY=your-super-secret-key-here
ENVIRONMENT=development
DEBUG=false
```

#### Шаг 4: Первый запуск

```bash
# 1. Сборка и запуск всех сервисов
docker-compose up -d

# 2. Проверка статуса сервисов
docker-compose ps

# 3. Просмотр логов
docker-compose logs -f app

# 4. Проверка health checks
curl http://localhost:8000/health/ready
```

---

## ⚙️ **КОНФИГУРИРОВАНИЕ СИСТЕМЫ**

### Основной конфигурационный файл

Файл `config/config.yaml` содержит все настройки системы:

```yaml
# =====================================
# Email Configuration
# =====================================
email:
  server: "imap.gmail.com"           # IMAP server
  port: 993                          # IMAP port (обычно 993 для SSL)
  username: "${EMAIL_USER}"          # Из .env файла
  password: "${EMAIL_PASS}"          # App-specific password
  allowed_senders:                   # Whitelist отправителей
    - "reports@company.com"
    - "analytics@partner.org"
    - "data@supplier.net"

# =====================================
# Database Configuration
# =====================================
database:
  host: "${POSTGRES_HOST}"
  port: "${POSTGRES_PORT}"
  user: "${POSTGRES_USER}"
  password: "${POSTGRES_PASSWORD}"
  name: "${POSTGRES_DB}"
  # Дополнительные настройки
  pool_size: 20                      # Размер connection pool
  max_overflow: 30                   # Максимальное переполнение
  pool_timeout: 30                   # Таймаут получения соединения
  pool_recycle: 3600                 # Переиспользование соединений

# =====================================
# SFTP Configuration
# =====================================
sftp:
  host: "${SFTP_HOST}"
  username: "${SFTP_USER}"
  key_path: "/root/.ssh/id_rsa"      # Путь к приватному ключу
  remote_path: "/upload/directory"    # Директория на SFTP сервере
  timeout: 30                        # Таймаут соединения
  max_retries: 3                     # Количество повторных попыток

# =====================================
# Notifications Configuration
# =====================================
notifications:
  email:
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "${EMAIL_USER}"
    password: "${EMAIL_PASS}"
    use_tls: true
    recipients:
      - "admin@company.com"
      - "ops@company.com"
  telegram:
    bot_token: "${TG_BOT_TOKEN}"
    chat_id: "${TG_CHAT_ID}"
    enable_notifications: true

# =====================================
# Scheduler Configuration
# =====================================
scheduler:
  interval_hours: 1                  # Интервал проверки почты (часы)
  timezone: "UTC"                    # Временная зона
  max_concurrent_jobs: 1             # Максимум одновременных задач
  misfire_grace_time: 300            # Время ожидания пропущенных задач

# =====================================
# File Processing Configuration
# =====================================
file_processing:
  max_file_size_mb: 50               # Максимальный размер файла
  temp_directory: "/tmp/processing"   # Временная директория
  csv_encoding: "utf-8-sig"          # Кодировка CSV (UTF-8 with BOM)
  csv_separator: ","                 # Разделитель CSV
  cleanup_temp_files: true           # Удалять временные файлы

# =====================================
# Logging Configuration
# =====================================
logging:
  config_file: "config/logging.yaml"
  log_to_file: true
  log_level: "INFO"                  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  max_log_size_mb: 10               # Максимальный размер лог-файла
  backup_count: 5                    # Количество backup файлов
```

### Конфигурация логгирования

Файл `config/logging.yaml`:

```yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt: "%Y-%m-%d %H:%M:%S"

  detailed:
    format: "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s [%(pathname)s]"
    datefmt: "%Y-%m-%d %H:%M:%S"

  json:
    format: '{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "line": %(lineno)d}'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout

  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: detailed
    filename: logs/app.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
    encoding: utf8

  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: json
    filename: logs/errors.log
    maxBytes: 10485760  # 10MB
    backupCount: 10
    encoding: utf8

loggers:
  src:
    level: DEBUG
    handlers: [console, file, error_file]
    propagate: false

  uvicorn:
    level: INFO
    handlers: [console, file]
    propagate: false

  sqlalchemy:
    level: WARNING
    handlers: [file]
    propagate: false

root:
  level: INFO
  handlers: [console, file]
```

### Настройка уведомлений

#### Email уведомления

1. **Настройка Gmail App Password:**
   ```
   1. Идите в Google Account settings
   2. Security → 2-Step Verification
   3. App passwords → Generate new password
   4. Скопируйте пароль в EMAIL_PASS
   ```

2. **Тестирование email:**
   ```bash
   # Отправка тестового уведомления
   curl -X POST http://localhost:8000/api/test/email-notification
   ```

#### Telegram уведомления

1. **Создание Telegram бота:**
   ```
   1. Найдите @BotFather в Telegram
   2. Отправьте /newbot
   3. Следуйте инструкциям
   4. Получите токен бота
   ```

2. **Получение Chat ID:**
   ```
   1. Добавьте бота в группу/канал
   2. Отправьте сообщение боту
   3. GET https://api.telegram.org/bot<TOKEN>/getUpdates
   4. Найдите chat_id в ответе
   ```

---

## 🎛️ **ЗАПУСК И УПРАВЛЕНИЕ**

### Команды запуска

#### Development режим:

```bash
# Запуск с горячей перезагрузкой
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Запуск только определенного сервиса
docker-compose up app

# Просмотр логов в реальном времени
docker-compose logs -f app
```

#### Production режим:

```bash
# Запуск в фоновом режиме
docker-compose up -d

# Проверка статуса всех сервисов
docker-compose ps

# Перезапуск определенного сервиса
docker-compose restart app

# Обновление сервиса без downtime
docker-compose up -d --no-deps app
```

### Управление жизненным циклом

#### Запуск системы:

```bash
# 1. Проверка конфигурации
docker-compose config

# 2. Сборка образов (если изменялся код)
docker-compose build

# 3. Запуск всех сервисов
docker-compose up -d

# 4. Проверка готовности
curl http://localhost:8000/health/ready
```

#### Остановка системы:

```bash
# Graceful остановка
docker-compose stop

# Принудительная остановка
docker-compose kill

# Полное удаление (ВНИМАНИЕ: удаляет данные!)
docker-compose down -v
```

#### Обновление системы:

```bash
# 1. Создание backup
docker-compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql

# 2. Остановка сервисов
docker-compose stop app

# 3. Обновление кода
git pull origin main

# 4. Пересборка образа
docker-compose build app

# 5. Запуск с новой версией
docker-compose up -d app
```

### Масштабирование

#### Горизонтальное масштабирование:

```bash
# Запуск нескольких экземпляров приложения
docker-compose up -d --scale app=3

# Проверка запущенных экземпляров
docker-compose ps app
```

#### Load Balancer конфигурация:

```yaml
# docker-compose.prod.yml
version: "3.8"
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app

  app:
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
```

---

## 📊 **МОНИТОРИНГ И ДИАГНОСТИКА**

### Health Checks

Система предоставляет несколько уровней проверки состояния:

#### 1. **Liveness Probe** (`/health/live`)
```bash
# Проверка живости сервиса
curl -I http://localhost:8000/health/live

# Ожидаемый ответ:
HTTP/1.1 204 No Content
```

**Назначение:** Проверяет, что процесс приложения работает
**Использование:** Kubernetes liveness probe
**Частота:** Каждые 10 секунд

#### 2. **Readiness Probe** (`/health/ready`)
```bash
# Проверка готовности к обработке запросов
curl -I http://localhost:8000/health/ready

# Успешный ответ:
HTTP/1.1 204 No Content

# При проблемах с зависимостями:
HTTP/1.1 503 Service Unavailable
```

**Назначение:** Проверяет доступность всех зависимостей
**Проверяемые компоненты:**
- PostgreSQL database connection
- SFTP server accessibility
- Email server connectivity
**Использование:** Kubernetes readiness probe
**Частота:** Каждые 30 секунд

#### 3. **Detailed Health Check** (`/health/detailed`)
```bash
# Получение детальной информации о состоянии
curl http://localhost:8000/health/detailed

# Пример успешного ответа:
{
  "status": "healthy",
  "checked_at": "2025-01-30T12:00:00Z",
  "dependencies": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15,
      "details": "Connection successful"
    },
    "sftp": {
      "status": "healthy",
      "response_time_ms": 120,
      "details": "Authentication successful"
    },
    "email": {
      "status": "healthy",
      "response_time_ms": 230,
      "details": "IMAP connection successful"
    }
  },
  "total_response_time_ms": 365
}
```

### Prometheus Метрики

Система экспортирует comprehensive метрики в формате Prometheus:

#### Получение метрик:
```bash
# Получение всех метрик
curl http://localhost:8000/metrics

# Фильтрация по типу метрики
curl http://localhost:8000/metrics | grep emails_processed_total
```

#### Основные метрики:

**1. Счетчики операций:**
```
# Обработанные email
emails_processed_total{status="success",sender_domain="company.com"} 150

# Конвертированные файлы
files_converted_total{size_category="small"} 45
files_converted_total{size_category="medium"} 12
files_converted_total{size_category="large"} 3

# SFTP загрузки
sftp_uploads_total{status="success",validated="true"} 58
sftp_uploads_total{status="failed",validated="false"} 2
```

**2. Ошибки по категориям:**
```
# Ошибки по типам
errors_by_type_total{error_type="ConnectionTimeout",component="email",severity="recoverable"} 5
errors_by_type_total{error_type="FileCorruption",component="processing",severity="recoverable"} 2
errors_by_type_total{error_type="SFTPAuthError",component="sftp",severity="critical"} 0
```

**3. Время выполнения (гистограммы):**
```
# Время обработки файлов
processing_duration_seconds_bucket{operation="file_conversion",le="1.0"} 45
processing_duration_seconds_bucket{operation="file_conversion",le="5.0"} 58
processing_duration_seconds_bucket{operation="file_conversion",le="10.0"} 60

# Health check времена
health_check_duration_seconds_bucket{dependency="database",le="0.1"} 120
health_check_duration_seconds_bucket{dependency="sftp",le="1.0"} 118
```

**4. Gauge метрики:**
```
# Активные задачи
active_processing_jobs 1

# Размер очереди email
email_queue_size 3

# Последняя успешная обработка (Unix timestamp)
last_successful_processing_timestamp 1706616000
```

**5. Информационные метрики:**
```
# Информация о приложении
app_info{version="1.0.0",environment="production"} 1
```

### Интеграция с Grafana

#### Dashboard конфигурация:

**Panel 1: Email Processing Rate**
```json
{
  "title": "Email Processing Rate",
  "type": "graph",
  "targets": [
    {
      "expr": "rate(emails_processed_total[5m])",
      "legendFormat": "{{status}} emails/sec"
    }
  ]
}
```

**Panel 2: Error Rate by Component**
```json
{
  "title": "Error Rate by Component",
  "type": "graph",
  "targets": [
    {
      "expr": "rate(errors_by_type_total[5m])",
      "legendFormat": "{{component}}: {{error_type}}"
    }
  ]
}
```

**Panel 3: System Health Status**
```json
{
  "title": "System Health",
  "type": "stat",
  "targets": [
    {
      "expr": "up{job=\"email-processor\"}",
      "legendFormat": "Service Up"
    }
  ]
}
```

### Логгирование

#### Структура логов:

**1. Application Logs** (`logs/app.log`):
```
2025-01-30 12:00:15 [INFO] email_reader: Starting email check cycle
2025-01-30 12:00:16 [INFO] email_reader: Found 3 new emails from allowed senders
2025-01-30 12:00:17 [INFO] file_processor: Processing file: report_20250130.xlsx (2.1MB)
2025-01-30 12:00:18 [INFO] file_processor: Converted to CSV: 1,245 rows exported
2025-01-30 12:00:19 [INFO] sftp_uploader: File uploaded and validated: RS_stoplist_20250130.csv
```

**2. Error Logs** (`logs/errors.log`):
```json
{
  "time": "2025-01-30 12:05:23",
  "level": "ERROR",
  "logger": "sftp_uploader",
  "message": "SFTP connection failed: Connection timeout",
  "module": "sftp_uploader",
  "line": 156,
  "error_type": "ConnectionTimeout",
  "retry_attempt": 2,
  "max_retries": 3
}
```

**3. Performance Logs** (`logs/performance.log`):
```json
{
  "time": "2025-01-30 12:00:20",
  "operation": "email_to_sftp_pipeline",
  "duration_ms": 4250,
  "file_size_mb": 2.1,
  "csv_rows": 1245,
  "status": "success"
}
```

#### Log Analysis Commands:

```bash
# Поиск ошибок за последний час
docker-compose exec app tail -f logs/errors.log | grep "$(date -d '1 hour ago' '+%Y-%m-%d %H')"

# Статистика по операциям
grep "operation_completed" logs/app.log | awk '{print $5}' | sort | uniq -c

# Мониторинг производительности
tail -f logs/performance.log | jq -r '[.operation, .duration_ms] | @tsv'

# Анализ ошибок по типам
grep ERROR logs/errors.log | jq -r .error_type | sort | uniq -c | sort -nr
```

---

## 🚨 **ОБРАБОТКА ОШИБОК**

Система включает enterprise-level систему обработки ошибок с автоматической категоризацией и восстановлением.

### Категории ошибок

#### 1. **CRITICAL Errors** 🔴
Требуют немедленного вмешательства и останавливают обработку:

```yaml
Типы:
  - DatabaseConnectionError: Потеря соединения с БД
  - SFTPAuthenticationError: Ошибка аутентификации SFTP
  - ConfigurationError: Критические ошибки конфигурации
  - PermissionError: Отсутствие прав доступа к файлам

Действия системы:
  - Немедленная остановка обработки
  - Отправка CRITICAL уведомлений администраторам
  - Логгирование с полным контекстом
  - Активация Circuit Breaker
```

**Пример лога CRITICAL ошибки:**
```json
{
  "timestamp": "2025-01-30T12:05:00Z",
  "level": "CRITICAL",
  "error_type": "DatabaseConnectionError",
  "component": "database",
  "message": "Failed to connect to PostgreSQL after 3 attempts",
  "context": {
    "host": "db",
    "port": 5432,
    "last_error": "connection refused",
    "retry_attempts": 3
  },
  "action_taken": "Circuit breaker opened, processing stopped"
}
```

#### 2. **RECOVERABLE Errors** 🟡
Обрабатываются автоматически с retry логикой:

```yaml
Типы:
  - EmailConnectionTimeout: Временная недоступность email
  - FileCorruptionError: Поврежденные файлы
  - SFTPTransferError: Временные сбои передачи
  - OSError: Временные файловые ошибки

Retry настройки:
  - EmailConnectionTimeout: 3 попытки, 30 сек delay
  - SFTPTransferError: 3 попытки, 30 сек delay
  - FileCorruptionError: 1 попытка, 5 сек delay
  - OSError: 2 попытки, 5 сек delay

Escalation:
  - После исчерпания попыток → CRITICAL
  - Уведомления при escalation
```

**Пример retry логики:**
```json
{
  "timestamp": "2025-01-30T12:03:15Z",
  "level": "WARNING",
  "error_type": "SFTPTransferError",
  "message": "SFTP transfer failed, attempting retry",
  "attempt": 2,
  "max_attempts": 3,
  "next_retry_in_seconds": 60,
  "exponential_backoff": true
}
```

#### 3. **WARNING Errors** 🟠
Логгируются без остановки обработки:

```yaml
Типы:
  - FileNotFoundError: Файл не найден (пропускается)
  - ValidationError: Ошибки валидации данных
  - EmailFilterError: Email не прошел фильтрацию

Действия:
  - Логгирование с контекстом
  - Продолжение обработки
  - Периодические summary отчеты
```

### Circuit Breaker Pattern

Защищает от каскадных сбоев внешних сервисов:

#### Состояния Circuit Breaker:

**1. CLOSED (Нормальная работа):**
```
- Все вызовы проходят к сервису
- Счетчик сбоев сбрасывается при успехе
- Переход в OPEN при достижении failure_threshold
```

**2. OPEN (Сервис недоступен):**
```
- Все вызовы блокируются
- Возвращается CircuitBreakerOpenError
- Переход в HALF_OPEN после recovery_timeout
```

**3. HALF_OPEN (Пробное восстановление):**
```
- Ограниченное количество пробных вызовов
- При успехе → CLOSED
- При сбое → обратно в OPEN
```

#### Конфигурация Circuit Breaker:

```python
# Для SFTP сервиса
SFTP_CIRCUIT_BREAKER = {
    "failure_threshold": 5,      # сбоев до открытия
    "recovery_timeout": 60.0,    # секунд до пробного вызова
    "success_threshold": 2,      # успехов для закрытия
    "timeout": 30.0             # таймаут вызова
}

# Для Email сервиса
EMAIL_CIRCUIT_BREAKER = {
    "failure_threshold": 3,
    "recovery_timeout": 120.0,
    "success_threshold": 1,
    "timeout": 45.0
}
```

### Graceful Degradation

Система автоматически адаптируется при частичных сбоях:

#### Уровни деградации:

**1. FULL_SERVICE:**
```
- Все компоненты работают нормально
- Полная функциональность доступна
- Стандартные SLA соблюдаются
```

**2. REDUCED_FEATURE:**
```
- SFTP недоступен → файлы сохраняются локально
- Notifications недоступны → логгирование в файл
- Metrics недоступны → базовое логгирование
```

**3. ESSENTIAL_ONLY:**
```
- Только email processing + file conversion
- Health checks отключены
- Расширенные метрики недоступны
```

**4. MAINTENANCE_MODE:**
```
- Email processing недоступен
- Только health checks работают
- Все новые запросы отклоняются
```

#### Automatic Fallback Strategies:

```python
# SFTP Fallback
if sftp_unavailable:
    save_files_locally("/backup/sftp_queue/")
    schedule_retry_when_available()

# Notifications Fallback
if telegram_unavailable:
    send_via_email()
if email_unavailable:
    log_to_file("/logs/notifications.log")

# Database Fallback
if database_unavailable:
    cache_operations_in_memory()
    persist_when_database_recovers()
```

### Recovery Mechanisms

#### Automatic Recovery:

```python
# Health Check Recovery
async def check_component_recovery():
    for component in failed_components:
        if await test_component_health(component):
            restore_component(component)
            log_recovery(component)
            send_recovery_notification(component)

# Retry Scheduling
@retry_with_exponential_backoff(
    max_attempts=3,
    base_delay=30,
    max_delay=300
)
async def retry_failed_operation():
    # Повторная попытка операции
    pass
```

#### Manual Recovery Commands:

```bash
# Принудительный сброс Circuit Breaker
curl -X POST http://localhost:8000/api/admin/circuit-breaker/reset

# Принудительное восстановление компонента
curl -X POST http://localhost:8000/api/admin/component/recover -d '{"component": "sftp"}'

# Очистка очереди ошибок
curl -X DELETE http://localhost:8000/api/admin/error-queue
```

---

## 🔌 **API ДОКУМЕНТАЦИЯ**

Система предоставляет REST API для мониторинга и управления.

### Автоматическая документация

Система автоматически генерирует interactive API документацию:

```bash
# Swagger UI
http://localhost:8000/docs

# ReDoc
http://localhost:8000/redoc

# OpenAPI JSON Schema
http://localhost:8000/openapi.json
```

### API Endpoints

#### Health Check Endpoints

**GET /health/live**
```yaml
Назначение: Liveness probe для Kubernetes
Ответ: 204 No Content (если жив)
Время ответа: < 100ms
Использование: kubectl, health checkers
```

**GET /health/ready**
```yaml
Назначение: Readiness probe, проверка зависимостей
Ответы:
  - 204 No Content: все зависимости здоровы
  - 503 Service Unavailable: проблемы с зависимостями
Проверяемые компоненты: Database, SFTP, Email
Время ответа: < 5 секунд
```

**GET /health/detailed**
```yaml
Назначение: Детальная диагностика системы
Формат ответа: JSON с подробной информацией
Использование: Отладка, мониторинг, dashboards

Пример ответа:
{
  "status": "healthy|degraded|unhealthy",
  "checked_at": "2025-01-30T12:00:00Z",
  "dependencies": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15,
      "details": "Connection successful",
      "last_check": "2025-01-30T12:00:00Z"
    },
    "sftp": {
      "status": "unhealthy",
      "response_time_ms": null,
      "details": "Connection timeout",
      "error": "Failed to connect after 30s",
      "last_successful_check": "2025-01-30T11:45:00Z"
    },
    "email": {
      "status": "healthy",
      "response_time_ms": 234,
      "details": "IMAP connection successful",
      "mailbox_count": 1250
    }
  },
  "degradation_level": "reduced_feature",
  "active_fallbacks": ["sftp_local_storage"],
  "total_response_time_ms": 249
}
```

#### Monitoring Endpoints

**GET /metrics**
```yaml
Назначение: Prometheus метрики
Формат: Prometheus exposition format
Content-Type: text/plain; version=0.0.4; charset=utf-8
Использование: Prometheus scraping, Grafana

Основные метрики:
  - emails_processed_total
  - files_converted_total
  - sftp_uploads_total
  - errors_by_type_total
  - processing_duration_seconds
  - health_check_duration_seconds
  - active_processing_jobs
  - email_queue_size
  - last_successful_processing_timestamp
  - app_info
```

**GET /**
```yaml
Назначение: Корневой endpoint, общая информация
Ответ:
{
  "message": "Service is running, scheduler is active.",
  "service": "Email & SFTP Processor",
  "version": "1.0.0",
  "status": "healthy",
  "uptime_seconds": 3600,
  "next_scheduled_run": "2025-01-30T13:00:00Z"
}
```

#### Administrative API (будущие версии)

**POST /api/admin/processing/trigger**
```yaml
Назначение: Принудительный запуск обработки
Требует: Admin токен
Тело запроса:
{
  "force": true,
  "specific_emails": ["email1@domain.com"]  # опционально
}
```

**GET /api/admin/stats**
```yaml
Назначение: Расширенная статистика
Ответ:
{
  "processing_stats": {
    "total_emails_processed": 1500,
    "total_files_converted": 1200,
    "total_sftp_uploads": 1180,
    "success_rate": 0.985,
    "average_processing_time_ms": 4250
  },
  "error_stats": {
    "critical_errors": 2,
    "recoverable_errors": 45,
    "warning_errors": 123,
    "recovery_rate": 0.956
  },
  "system_stats": {
    "uptime_hours": 168,
    "memory_usage_mb": 256,
    "disk_usage_gb": 12.5,
    "cpu_usage_percent": 15.3
  }
}
```

### Rate Limiting

Все API endpoints защищены rate limiting:

```yaml
Default limits:
  - /health/*: 600 requests/minute (10/second)
  - /metrics: 60 requests/minute (1/second)
  - /api/*: 100 requests/minute (1.67/second)
  - Other endpoints: 100 requests/minute

Rate limit headers:
  - X-RateLimit-Limit: Maximum requests
  - X-RateLimit-Remaining: Remaining requests
  - X-RateLimit-Reset: Reset time (Unix timestamp)

Rate limit exceeded response:
  - Status: 429 Too Many Requests
  - Body: {"error": "Rate limit exceeded. Please try again later."}
  - Header: Retry-After: 60
```

### API Client Examples

#### Python client:
```python
import requests
import time

class EmailProcessorClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def check_health(self):
        """Проверка состояния системы"""
        response = requests.get(f"{self.base_url}/health/detailed")
        return response.json()

    def get_metrics(self):
        """Получение метрик Prometheus"""
        response = requests.get(f"{self.base_url}/metrics")
        return response.text

    def wait_for_ready(self, timeout=300):
        """Ожидание готовности системы"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/health/ready")
                if response.status_code == 204:
                    return True
            except requests.RequestException:
                pass
            time.sleep(10)
        return False

# Использование
client = EmailProcessorClient()
if client.wait_for_ready():
    health = client.check_health()
    print(f"System status: {health['status']}")
```

#### Bash client:
```bash
#!/bin/bash
# Email Processor API Client

BASE_URL="http://localhost:8000"

check_health() {
    curl -s "$BASE_URL/health/detailed" | jq -r '.status'
}

get_metrics() {
    curl -s "$BASE_URL/metrics" | grep -E "^(emails_processed|files_converted|sftp_uploads)_total"
}

wait_for_ready() {
    local timeout=${1:-300}
    local elapsed=0

    while [ $elapsed -lt $timeout ]; do
        if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health/ready" | grep -q "204"; then
            echo "System is ready"
            return 0
        fi
        sleep 10
        elapsed=$((elapsed + 10))
    done

    echo "Timeout waiting for system to be ready"
    return 1
}

# Использование
if wait_for_ready; then
    echo "Health status: $(check_health)"
    echo "Key metrics:"
    get_metrics
fi
```

---

## 🔒 **БЕЗОПАСНОСТЬ И ПРОИЗВОДИТЕЛЬНОСТЬ**

### Система безопасности

#### 1. **Authentication & Authorization**

**SSH Key-based Authentication для SFTP:**
```bash
# Генерация secure ключей
ssh-keygen -t rsa -b 4096 -f ~/.ssh/sftp_key

# Установка правильных permissions
chmod 600 ~/.ssh/sftp_key
chmod 644 ~/.ssh/sftp_key.pub

# Конфигурация в docker-compose.yml
volumes:
  - ~/.ssh/sftp_key:/root/.ssh/id_rsa:ro
```

**Email Authentication:**
```yaml
# App-specific passwords для Gmail
email:
  username: "service-account@company.com"
  password: "app-specific-password"  # НЕ основной пароль!

# OAuth2 для корпоративных email (будущие версии)
oauth2:
  client_id: "${EMAIL_CLIENT_ID}"
  client_secret: "${EMAIL_CLIENT_SECRET}"
  tenant_id: "${EMAIL_TENANT_ID}"
```

#### 2. **Network Security**

**Container Network Isolation:**
```yaml
# docker-compose.yml
networks:
  backend:
    driver: bridge
    internal: true  # Изоляция от внешней сети
  frontend:
    driver: bridge

services:
  app:
    networks:
      - backend
      - frontend
  db:
    networks:
      - backend  # Только внутренняя сеть
```

**Firewall Rules (iptables):**
```bash
# Разрешить только необходимые порты
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT  # API
iptables -A INPUT -p tcp --dport 22 -j ACCEPT    # SSH
iptables -A INPUT -p tcp --dport 443 -j ACCEPT   # HTTPS

# Заблокировать все остальное
iptables -A INPUT -j DROP
```

#### 3. **Data Security**

**Encryption at Rest:**
```yaml
# PostgreSQL с шифрованием
db:
  environment:
    POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256"
  volumes:
    - type: volume
      source: postgres_data
      target: /var/lib/postgresql/data
      volume:
        driver_opts:
          type: "encrypted"
```

**Encryption in Transit:**
```yaml
# TLS для всех подключений
email:
  use_tls: true
  verify_cert: true

sftp:
  strict_host_key_checking: true

notifications:
  email:
    use_tls: true
  telegram:
    verify_ssl: true
```

#### 4. **Secrets Management**

**Environment Variables Security:**
```bash
# .env файл с правильными permissions
touch .env
chmod 600 .env  # Только владелец может читать

# Docker secrets (production)
echo "password123" | docker secret create postgres_password -
```

**Vault Integration (production):**
```python
# config/vault_config.py
import hvac

class VaultConfig:
    def __init__(self):
        self.client = hvac.Client(url='https://vault.company.com')

    def get_secret(self, path):
        response = self.client.secrets.kv.v2.read_secret_version(path=path)
        return response['data']['data']

# Использование
vault = VaultConfig()
db_creds = vault.get_secret('email-processor/database')
```

#### 5. **Rate Limiting & DDoS Protection**

**Multi-tier Rate Limiting:**
```python
# Конфигурация по endpoints
RATE_LIMITS = {
    "/health/*": {
        "requests_per_minute": 600,  # Health checks
        "strategy": "fixed_window"
    },
    "/metrics": {
        "requests_per_minute": 60,   # Prometheus scraping
        "strategy": "sliding_window"
    },
    "/api/*": {
        "requests_per_minute": 100,  # API calls
        "strategy": "token_bucket",
        "burst_allowance": 20
    }
}
```

**IP-based Blocking:**
```python
# Автоматическая блокировка агрессивных IP
SECURITY_RULES = {
    "block_threshold": 1000,      # запросов за час
    "block_duration": 3600,       # блокировка на час
    "whitelist_ips": [
        "10.0.0.0/8",            # Внутренняя сеть
        "192.168.1.100"          # Monitoring сервер
    ]
}
```

### Performance Optimization

#### 1. **Database Performance**

**Connection Pooling:**
```yaml
database:
  pool_size: 20                 # Основной пул соединений
  max_overflow: 30              # Дополнительные соединения
  pool_timeout: 30              # Таймаут получения соединения
  pool_recycle: 3600            # Переиспользование соединений (1 час)
  pool_pre_ping: true           # Проверка соединения перед использованием
```

**Индексирование:**
```sql
-- Оптимизированные индексы
CREATE INDEX CONCURRENTLY idx_processed_files_message_id
    ON processed_files(message_id);

CREATE INDEX CONCURRENTLY idx_processed_files_processed_at
    ON processed_files(processed_at DESC);

CREATE INDEX CONCURRENTLY idx_operation_logs_created_at
    ON operation_logs(created_at DESC);

CREATE INDEX CONCURRENTLY idx_operation_logs_operation_type
    ON operation_logs(operation_type, status);
```

**Query Optimization:**
```python
# Efficient queries с лимитами
async def get_recent_files(limit: int = 100):
    query = select(ProcessedFile).order_by(
        ProcessedFile.processed_at.desc()
    ).limit(limit)
    return await session.execute(query)

# Batch операции
async def bulk_insert_logs(logs: List[OperationLog]):
    await session.execute(
        insert(OperationLog),
        [log.dict() for log in logs]
    )
```

#### 2. **Memory Optimization**

**Streaming File Processing:**
```python
# Обработка больших файлов по частям
async def process_large_file(file_path: Path):
    chunk_size = 10000  # строк

    async with aiofiles.open(file_path, 'rb') as f:
        for chunk in pd.read_excel(f, chunksize=chunk_size):
            processed_chunk = await process_chunk(chunk)
            await save_chunk_to_csv(processed_chunk)

            # Освобождение памяти
            del chunk, processed_chunk
            gc.collect()
```

**Memory Monitoring:**
```python
import psutil
import asyncio

async def monitor_memory():
    process = psutil.Process()

    while True:
        memory_mb = process.memory_info().rss / 1024 / 1024

        if memory_mb > 500:  # MB
            logger.warning(f"High memory usage: {memory_mb:.1f}MB")
            gc.collect()  # Принудительная сборка мусора

        await asyncio.sleep(60)
```

#### 3. **Async Optimization**

**Connection Pooling для внешних сервисов:**
```python
# SFTP Connection Pool
class SFTPConnectionPool:
    def __init__(self, max_connections=5):
        self.pool = asyncio.Queue(maxsize=max_connections)
        self.max_connections = max_connections

    async def get_connection(self):
        try:
            return await asyncio.wait_for(
                self.pool.get(),
                timeout=30
            )
        except asyncio.TimeoutError:
            return await self.create_connection()
```

**Parallel Processing:**
```python
# Параллельная обработка файлов
async def process_multiple_files(files: List[Path]):
    semaphore = asyncio.Semaphore(3)  # Ограничение concurrent операций

    async def process_single_file(file_path):
        async with semaphore:
            return await process_file(file_path)

    tasks = [process_single_file(f) for f in files]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return results
```

#### 4. **Caching Strategy**

**Redis Caching (для production):**
```python
import aioredis

class CacheService:
    def __init__(self):
        self.redis = aioredis.from_url("redis://localhost:6379")

    async def cache_file_hash(self, file_path: str, hash_value: str):
        await self.redis.setex(
            f"file_hash:{file_path}",
            3600,  # TTL 1 час
            hash_value
        )

    async def get_cached_hash(self, file_path: str) -> Optional[str]:
        return await self.redis.get(f"file_hash:{file_path}")
```

**In-Memory Caching:**
```python
from functools import lru_cache
import time

class InMemoryCache:
    def __init__(self, ttl=300):  # 5 минут TTL
        self.cache = {}
        self.ttl = ttl

    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key, value):
        self.cache[key] = (value, time.time())
```

### Resource Monitoring

#### System Resource Monitoring:

```python
# Continuous resource monitoring
async def monitor_system_resources():
    while True:
        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory Usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # Disk Usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100

        # Network I/O
        network = psutil.net_io_counters()

        # Log если превышены пороги
        if cpu_percent > 80:
            logger.warning(f"High CPU usage: {cpu_percent}%")

        if memory_percent > 85:
            logger.warning(f"High memory usage: {memory_percent}%")

        if disk_percent > 90:
            logger.error(f"High disk usage: {disk_percent}%")

        # Метрики для Prometheus
        await update_system_metrics(cpu_percent, memory_percent, disk_percent)

        await asyncio.sleep(30)
```

#### Performance Benchmarks:

```python
# Benchmark результаты для системы
PERFORMANCE_TARGETS = {
    "email_check_duration": "< 30 seconds",
    "file_conversion_rate": "> 10 MB/second",
    "sftp_upload_rate": "> 5 MB/second",
    "database_query_time": "< 100ms",
    "health_check_response": "< 1 second",
    "memory_usage": "< 512 MB",
    "cpu_usage": "< 50% average"
}
```

---

## 🔧 **УСТРАНЕНИЕ НЕПОЛАДОК**

### Диагностика проблем

#### 1. **Система не запускается**

**Проблема:** Docker контейнеры не стартуют
```bash
# Диагностика
docker-compose ps
docker-compose logs app

# Типичные причины:
# 1. Неправильные permissions на .env файле
chmod 600 .env

# 2. Отсутствующие переменные окружения
grep -v '^#\|^$' .env  # Проверить все переменные

# 3. Конфликт портов
netstat -tulpn | grep :8000

# 4. Недостаток места на диске
df -h
```

**Проблема:** База данных недоступна
```bash
# Проверка состояния PostgreSQL
docker-compose exec db pg_isready -U $POSTGRES_USER

# Проверка логов БД
docker-compose logs db

# Решение проблем с данными
docker-compose down
docker volume prune  # ВНИМАНИЕ: удаляет данные!
docker-compose up -d
```

#### 2. **Проблемы с подключением к Email**

**Проблема:** Не удается подключиться к IMAP
```bash
# Проверка сетевого соединения
telnet imap.gmail.com 993

# Тестирование IMAP подключения
python3 -c "
import imaplib
try:
    mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    mail.login('$EMAIL_USER', '$EMAIL_PASS')
    print('IMAP connection successful')
    mail.logout()
except Exception as e:
    print(f'IMAP connection failed: {e}')
"
```

**Типичные решения:**
- Убедитесь, что используется App-specific password, а не основной пароль
- Проверьте, что включена 2FA в Google Account
- Убедитесь, что "Less secure app access" выключен (используйте App passwords)

#### 3. **Проблемы со SFTP**

**Проблема:** Ошибки аутентификации SFTP
```bash
# Тестирование SFTP подключения
sftp -i ~/.ssh/id_rsa -P 2222 sftpuser@localhost

# Проверка SSH ключей
ssh-keygen -y -f ~/.ssh/id_rsa  # Должен вывести публичный ключ

# Проверка permissions
ls -la ~/.ssh/
# id_rsa должен быть 600, id_rsa.pub может быть 644
```

**Типичные решения:**
- Убедитесь, что приватный ключ имеет правильные permissions (600)
- Проверьте, что публичный ключ добавлен на SFTP сервер
- Проверьте формат ключей (OpenSSH vs PEM)

#### 4. **Проблемы с обработкой файлов**

**Проблема:** Файлы не конвертируются
```bash
# Проверка логов обработки файлов
docker-compose logs app | grep file_processor

# Тестирование конвертации вручную
docker-compose exec app python -c "
import pandas as pd
df = pd.read_excel('/path/to/test.xlsx')
df.to_csv('/tmp/test.csv', index=False, encoding='utf-8-sig')
print('Conversion successful')
"
```

**Типичные причины:**
- Поврежденные Excel файлы
- Недостаток памяти для больших файлов
- Неправильная кодировка

#### 5. **Performance Issues**

**Проблема:** Медленная обработка
```bash
# Мониторинг ресурсов
docker stats

# Проверка размеров файлов
find storage/ -name "*.xlsx" -exec ls -lh {} \;

# Анализ медленных запросов БД
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;"
```

### Общие команды диагностики

#### System Health Check:
```bash
#!/bin/bash
# comprehensive_health_check.sh

echo "=== Email Processor Health Check ==="

# 1. Container Status
echo "1. Container Status:"
docker-compose ps

# 2. Resource Usage
echo -e "\n2. Resource Usage:"
docker stats --no-stream

# 3. Disk Space
echo -e "\n3. Disk Space:"
df -h

# 4. API Health
echo -e "\n4. API Health:"
curl -s http://localhost:8000/health/detailed | jq -r '.status'

# 5. Database Status
echo -e "\n5. Database Connection:"
docker-compose exec -T db pg_isready -U $POSTGRES_USER

# 6. SFTP Test
echo -e "\n6. SFTP Test:"
timeout 10 sftp -i ~/.ssh/id_rsa -P 2222 sftpuser@localhost <<< "ls" 2>/dev/null && echo "SFTP OK" || echo "SFTP Failed"

# 7. Recent Errors
echo -e "\n7. Recent Errors (last 10):"
docker-compose logs app --tail=100 | grep ERROR | tail -10

echo -e "\nHealth check completed."
```

#### Log Analysis:
```bash
#!/bin/bash
# analyze_logs.sh

echo "=== Log Analysis ==="

# Error summary
echo "1. Error Summary (last 24 hours):"
docker-compose logs app --since 24h | grep ERROR | awk '{print $5}' | sort | uniq -c | sort -nr

# Performance analysis
echo -e "\n2. Performance Analysis:"
docker-compose logs app --since 1h | grep "operation_completed" |
awk '{print $NF}' | sort -n |
awk '{
    if(NR==1) min=$1
    max=$1
    sum+=$1
}
END {
    print "Min:", min "ms"
    print "Max:", max "ms"
    print "Avg:", sum/NR "ms"
}'

# Success rate
echo -e "\n3. Success Rate (last hour):"
total=$(docker-compose logs app --since 1h | grep -c "processing_completed")
success=$(docker-compose logs app --since 1h | grep "processing_completed" | grep -c "success")
if [ $total -gt 0 ]; then
    echo "Success rate: $(echo "scale=2; $success * 100 / $total" | bc)% ($success/$total)"
else
    echo "No processing completed in the last hour"
fi
```

### Emergency Procedures

#### 1. **Service Recovery**
```bash
# Полное восстановление сервиса
#!/bin/bash
echo "Starting emergency recovery..."

# 1. Остановка всех сервисов
docker-compose down

# 2. Backup текущих данных
docker run --rm -v rs-stoplist-project_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup_$(date +%Y%m%d_%H%M%S).tar.gz /data

# 3. Очистка и пересоздание
docker system prune -f
docker-compose build --no-cache

# 4. Запуск с проверками
docker-compose up -d
sleep 30

# 5. Проверка восстановления
curl -f http://localhost:8000/health/ready && echo "Service recovered successfully" || echo "Recovery failed"
```

#### 2. **Data Recovery**
```bash
# Восстановление из backup
#!/bin/bash
backup_file=$1

if [ -z "$backup_file" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "Restoring from backup: $backup_file"

# Остановка сервисов
docker-compose stop

# Восстановление данных
docker run --rm -v rs-stoplist-project_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/$backup_file -C /

# Перезапуск
docker-compose start

echo "Restore completed"
```

#### 3. **Performance Tuning**
```bash
# Оптимизация производительности
#!/bin/bash

echo "Applying performance optimizations..."

# 1. Очистка старых логов
find logs/ -name "*.log" -mtime +7 -delete

# 2. Vacuum БД
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "VACUUM ANALYZE;"

# 3. Очистка Docker
docker system prune -f

# 4. Restart сервисов
docker-compose restart

echo "Performance optimization completed"
```

---

## ❓ **ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ**

### Общие вопросы

**Q: Как часто система проверяет новые email?**
A: По умолчанию каждый час. Настраивается в `config/config.yaml`:
```yaml
scheduler:
  interval_hours: 1  # Можно изменить на 0.5 (30 мин) или любое значение
```

**Q: Какой максимальный размер файла поддерживается?**
A: По умолчанию 50MB. Настраивается в конфигурации:
```yaml
file_processing:
  max_file_size_mb: 50  # Увеличьте при необходимости
```

**Q: Можно ли обрабатывать файлы из нескольких email аккаунтов?**
A: Да, добавьте несколько аккаунтов в конфигурацию:
```yaml
email:
  accounts:
    - server: "imap.gmail.com"
      username: "${EMAIL_USER_1}"
      password: "${EMAIL_PASS_1}"
    - server: "imap.outlook.com"
      username: "${EMAIL_USER_2}"
      password: "${EMAIL_PASS_2}"
```

### Технические вопросы

**Q: Как добавить нового отправителя в whitelist?**
A: Отредактируйте `config/config.yaml`:
```yaml
email:
  allowed_senders:
    - "existing@sender.com"
    - "new@sender.com"  # Добавить здесь
```
Перезапуск не требуется - конфигурация загружается динамически.

**Q: Как изменить формат выходного CSV файла?**
A: Настройте в конфигурации:
```yaml
file_processing:
  csv_encoding: "utf-8-sig"  # или "utf-8", "cp1251"
  csv_separator: ","         # или ";" для Excel
  output_format: "RS_stoplist_{YYYYMMDD}.csv"
```

**Q: Можно ли отключить SFTP загрузку и только конвертировать файлы?**
A: Да, установите переменную окружения:
```bash
DISABLE_SFTP_UPLOAD=true
```
Файлы будут сохраняться только локально.

### Проблемы и решения

**Q: Система показывает "Service Unavailable" при проверке /health/ready**
A: Проверьте состояние зависимостей:
```bash
# Проверка детального статуса
curl http://localhost:8000/health/detailed

# Проверка конкретных компонентов
docker-compose exec db pg_isready
sftp -i ~/.ssh/id_rsa -P 2222 sftpuser@localhost
```

**Q: Файлы обрабатываются, но не появляются на SFTP сервере**
A: Проверьте валидацию файлов:
```bash
# Проверьте логи SFTP операций
docker-compose logs app | grep sftp_uploader

# Проверьте права доступа на SFTP сервере
sftp -i ~/.ssh/id_rsa user@sftp-server
ls -la /upload/directory/
```

**Q: Высокое потребление памяти**
A: Оптимизируйте обработку больших файлов:
```yaml
file_processing:
  chunk_size: 10000      # Обработка по частям
  max_file_size_mb: 20   # Ограничение размера
  cleanup_temp_files: true
```

### Мониторинг и алерты

**Q: Как настроить алерты в Grafana?**
A: Создайте алерт на основе метрик:
```json
{
  "alert": {
    "conditions": [
      {
        "query": "A",
        "reducer": "last",
        "type": "query"
      }
    ],
    "executionErrorState": "alerting",
    "for": "5m",
    "frequency": "10s",
    "handler": 1,
    "name": "Email Processing Failure",
    "noDataState": "no_data",
    "notifications": []
  },
  "targets": [
    {
      "expr": "rate(errors_by_type_total{severity=\"critical\"}[5m])",
      "refId": "A"
    }
  ]
}
```

**Q: Как получать уведомления о критических ошибках?**
A: Настройте Telegram/Email уведомления:
```yaml
notifications:
  telegram:
    bot_token: "${TG_BOT_TOKEN}"
    chat_id: "${TG_CHAT_ID}"
    alert_levels: ["critical", "error"]  # Только важные
  email:
    recipients: ["admin@company.com"]
    alert_levels: ["critical"]  # Только критические
```

### Производительность

**Q: Как ускорить обработку больших файлов?**
A: Несколько оптимизаций:
```yaml
# 1. Увеличьте память для контейнера
services:
  app:
    deploy:
      resources:
        limits:
          memory: 2G

# 2. Настройте параллельную обработку
file_processing:
  parallel_workers: 3
  chunk_size: 50000

# 3. Используйте SSD диски для временных файлов
file_processing:
  temp_directory: "/tmp/fast_ssd/"
```

**Q: Как масштабировать систему для большой нагрузки?**
A: Горизонтальное масштабирование:
```bash
# 1. Запуск нескольких инстансов
docker-compose up -d --scale app=3

# 2. Load balancer (nginx)
upstream email_processor {
    server app:8000;
    server app:8000;
    server app:8000;
}

# 3. Разделение по email аккаунтам
# Каждый инстанс обрабатывает свой набор аккаунтов
```

### Безопасность

**Q: Как обеспечить безопасность в production?**
A: Следуйте security checklist:
```bash
# 1. Используйте HTTPS
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
}

# 2. Ограничьте доступ к API
iptables -A INPUT -p tcp --dport 8000 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j DROP

# 3. Регулярно обновляйте зависимости
docker-compose pull
docker-compose build --no-cache

# 4. Мониторьте безопасность
docker scan email-processor:latest
```

**Q: Как защитить секретные данные?**
A: Используйте external secrets:
```yaml
# docker-compose.prod.yml
services:
  app:
    secrets:
      - postgres_password
      - email_password

secrets:
  postgres_password:
    external: true
  email_password:
    external: true
```

---

## 📞 **ПОДДЕРЖКА И КОНТАКТЫ**

### Техническая поддержка

**Уровень 1 - Самообслуживание:**
- Данное руководство пользователя
- Автоматические health checks: `/health/detailed`
- Логи приложения: `docker-compose logs app`
- Метрики мониторинга: `/metrics`

**Уровень 2 - Диагностика:**
- Запуск диагностических скриптов
- Анализ performance метрик
- Проверка конфигурации системы

**Уровень 3 - Escalation:**
- Критические ошибки системы
- Проблемы безопасности
- Запросы на новый функционал

### Отчетность об ошибках

При обращении в поддержку приложите:

1. **System Information:**
```bash
# Соберите системную информацию
./scripts/collect_system_info.sh > system_info.txt
```

2. **Logs Package:**
```bash
# Соберите логи за последние 24 часа
docker-compose logs --since 24h > logs_24h.txt
```

3. **Configuration:**
```bash
# Соберите конфигурацию (удалите секреты!)
cp config/config.yaml config_anonymized.yaml
sed -i 's/password:.*/password: [REDACTED]/' config_anonymized.yaml
```

### Документация и ресурсы

- **API Documentation:** http://localhost:8000/docs
- **Monitoring Dashboard:** http://localhost:3000 (Grafana)
- **Database Admin:** http://localhost:8080 (Adminer)

### Обновления и версии

**Проверка текущей версии:**
```bash
curl http://localhost:8000/ | jq -r '.version'
```

**Планируемые обновления:**
- v1.1.0: OAuth2 поддержка для корпоративных email
- v1.2.0: Web UI для администрирования
- v1.3.0: Kubernetes Helm charts
- v2.0.0: Микросервисная архитектура

---

**© 2025 Система автоматизированной обработки Excel-файлов**
**Версия документации:** 1.0
**Последнее обновление:** 30 января 2025 г.
