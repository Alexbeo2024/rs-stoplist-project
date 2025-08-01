# 🔧 **ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ - ПОЛНОЕ РУКОВОДСТВО**

*Автоматизированная система обработки Excel-файлов из email вложений*

---

## 📋 **ОБЗОР**

Данная система использует переменные окружения для конфигурации всех основных компонентов. Переменные разделены на несколько категорий в зависимости от их назначения.

---

## 📧 **1. ДОСТУП К ПОЧТЕ ДЛЯ ЧТЕНИЯ ФАЙЛОВ**

### **Основные переменные:**

| Переменная | Описание | Пример | Обязательная |
|------------|----------|---------|--------------|
| `EMAIL_USER` | Email адрес для мониторинга | `aak@jugoexsim.rs` | ✅ |
| `EMAIL_PASS` | Пароль или App Password | `your_app_password` | ✅ |

### **Дополнительные настройки (в config.yaml):**

```yaml
email:
  server: "imap.gmail.com"        # IMAP сервер
  port: 993                       # Порт IMAP (993 для SSL)
  username: "${EMAIL_USER}"       # Ссылка на переменную
  password: "${EMAIL_PASS}"       # Ссылка на переменную
  allowed_senders:                # Whitelist отправителей
    - "reports@company.com"
    - "data@partner.com"
```

### **Важные детали:**
- **App Password**: Для Gmail/Outlook требуется App Password, не основной пароль
- **SSL/TLS**: Система использует защищенное соединение (IMAP SSL)
- **Whitelist**: Обрабатываются только письма от разрешенных отправителей
- **Deduplication**: Предотвращение повторной обработки по Message-ID

---

## 📤 **2. ОТПРАВКА EMAIL УВЕДОМЛЕНИЙ**

### **Основные переменные:**

| Переменная | Описание | Пример | Обязательная |
|------------|----------|---------|--------------|
| `SMTP_SERVER` | SMTP сервер для отправки | `smtp.jugoexsim.rs` | ✅ |
| `SMTP_PORT` | Порт SMTP сервера | `465` или `587` | ✅ |
| `SMTP_USER` | Логин для SMTP | `notifications@company.com` | ✅ |
| `SMTP_PASS` | Пароль для SMTP | `smtp_password` | ✅ |

### **Конфигурация уведомлений:**

```yaml
notifications:
  email:
    smtp_server: "${SMTP_SERVER}"
    smtp_port: ${SMTP_PORT}
    username: "${SMTP_USER}"
    password: "${SMTP_PASS}"
    use_tls: true                 # Использовать TLS
    recipients:                   # Список получателей
      - "admin@company.com"
      - "ops@company.com"
      - "monitoring@company.com"
```

### **Типы уведомлений:**
- **SUCCESS**: Успешная обработка файлов
- **ERROR**: Ошибки подключения, конвертации, загрузки
- **WARNING**: Нестандартные ситуации
- **CRITICAL**: Критические сбои системы

---

## 📱 **3. TELEGRAM УВЕДОМЛЕНИЯ (ОПЦИОНАЛЬНО)**

### **Основные переменные:**

| Переменная | Описание | Пример | Обязательная |
|------------|----------|---------|--------------|
| `TG_BOT_TOKEN` | Токен Telegram бота | `1234567890:ABC...` | ❌ |
| `TG_CHAT_ID` | ID чата для уведомлений | `-1001234567890` | ❌ |

### **Настройка Telegram:**

```yaml
notifications:
  telegram:
    bot_token: "${TG_BOT_TOKEN}"
    chat_id: "${TG_CHAT_ID}"
    enabled: true               # Включить/выключить
```

### **Как включить/выключить:**

#### **✅ Включить Telegram:**
1. Создайте бота через @BotFather
2. Получите `bot_token`
3. Добавьте бота в группу/канал
4. Получите `chat_id`
5. Установите `enabled: true` в config.yaml
6. Добавьте переменные в `.env`

#### **❌ Отключить Telegram:**
1. Установите `enabled: false` в config.yaml
2. Или удалите секцию `telegram` полностью
3. Или не устанавливайте `TG_BOT_TOKEN` и `TG_CHAT_ID`

---

## 🚀 **4. ОТПРАВКА ФАЙЛОВ НА SFTP СЕРВЕР**

### **Основные переменные:**

| Переменная | Описание | Пример | Обязательная |
|------------|----------|---------|--------------|
| `SFTP_HOST` | Хост SFTP сервера | `sftp.company.com` | ✅ |
| `SFTP_PORT` | Порт SFTP | `22` | ❌ |
| `SFTP_USER` | Имя пользователя | `excel_processor` | ✅ |
| `SFTP_PASS` | Пароль (если не ключ) | `sftp_password` | ❌* |
| `SFTP_KEY_PATH` | Путь к SSH ключу | `/root/.ssh/id_rsa` | ❌* |

*Обязательна либо `SFTP_PASS`, либо `SFTP_KEY_PATH`

### **Конфигурация SFTP:**

```yaml
sftp:
  host: "${SFTP_HOST}"
  port: ${SFTP_PORT:-22}          # Порт по умолчанию 22
  username: "${SFTP_USER}"
  password: "${SFTP_PASS}"        # Для аутентификации по паролю
  key_path: "${SFTP_KEY_PATH}"    # Для аутентификации по ключу
  remote_path: "/upload/excel"    # Базовая папка на сервере
  timeout: 30                     # Таймаут соединения
  max_retries: 3                  # Количество повторов
  verify_upload: true             # Проверка целостности
```

### **Типы аутентификации:**

#### **🔐 По паролю:**
```bash
SFTP_HOST=sftp.company.com
SFTP_USER=excel_user
SFTP_PASS=secure_password
```

#### **🔑 По SSH ключу:**
```bash
SFTP_HOST=sftp.company.com
SFTP_USER=excel_user
SFTP_KEY_PATH=/path/to/private_key
```

---

## 🗄️ **5. БАЗА ДАННЫХ**

### **Основные переменные:**

| Переменная | Описание | Пример | Обязательная |
|------------|----------|---------|--------------|
| `POSTGRES_HOST` | Хост PostgreSQL | `db` | ✅ |
| `POSTGRES_PORT` | Порт PostgreSQL | `5432` | ✅ |
| `POSTGRES_USER` | Пользователь БД | `emailprocessor` | ✅ |
| `POSTGRES_PASSWORD` | Пароль БД | `secure_password_123` | ✅ |
| `POSTGRES_DB` | Имя базы данных | `email_processor_db` | ✅ |

### **Назначение базы данных:**
- **Логирование операций** (успех/ошибки)
- **Метаданные файлов** (хеши, пути, даты)
- **Дедупликация** (предотвращение повторной обработки)
- **Аудит и мониторинг** системы

---

## 🔒 **6. БЕЗОПАСНОСТЬ**

### **Основные переменные:**

| Переменная | Описание | Пример | Обязательная |
|------------|----------|---------|--------------|
| `SECRET_KEY` | Секретный ключ приложения | `long_random_string` | ✅ |
| `JWT_SECRET_KEY` | Ключ для JWT токенов | `another_random_string` | ❌ |
| `ENVIRONMENT` | Режим работы | `production` | ✅ |

---

## 📊 **7. МОНИТОРИНГ И ЛОГИРОВАНИЕ**

### **Основные переменные:**

| Переменная | Описание | Пример | Обязательная |
|------------|----------|---------|--------------|
| `LOG_LEVEL` | Уровень логирования | `INFO` | ❌ |
| `DEBUG` | Режим отладки | `false` | ❌ |

### **Уровни логирования:**
- **DEBUG**: Детальная отладочная информация
- **INFO**: Общая информация о работе
- **WARNING**: Предупреждения
- **ERROR**: Ошибки
- **CRITICAL**: Критические сбои

---

## 📝 **ПРИМЕР ПОЛНОГО .env ФАЙЛА**

```bash
# =====================================
# EMAIL MONITORING (ЧТЕНИЕ ФАЙЛОВ)
# =====================================
EMAIL_USER=aak@jugoexsim.rs
EMAIL_PASS=your_app_password_here

# =====================================
# EMAIL NOTIFICATIONS (ОТПРАВКА УВЕДОМЛЕНИЙ)
# =====================================
SMTP_SERVER=smtp.jugoexsim.rs
SMTP_PORT=465
SMTP_USER=notifications@jugoexsim.rs
SMTP_PASS=smtp_password_here

# =====================================
# TELEGRAM (ОПЦИОНАЛЬНО)
# =====================================
TG_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyZ
TG_CHAT_ID=-1001234567890

# =====================================
# SFTP UPLOAD
# =====================================
SFTP_HOST=sftp.company.com
SFTP_PORT=22
SFTP_USER=excel_processor
SFTP_PASS=sftp_password
# SFTP_KEY_PATH=/path/to/private_key  # Альтернатива паролю

# =====================================
# DATABASE
# =====================================
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_USER=emailprocessor
POSTGRES_PASSWORD=secure_password_123
POSTGRES_DB=email_processor_db

# =====================================
# SECURITY
# =====================================
SECRET_KEY=your_super_secret_key_here_minimum_32_chars
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

---

## 🔧 **НАСТРОЙКА ПО ЭТАПАМ**

### **1️⃣ Минимальная конфигурация:**
```bash
# Только обязательные переменные
EMAIL_USER=your@email.com
EMAIL_PASS=app_password
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRES_DB=db_name
SFTP_HOST=sftp.server.com
SFTP_USER=sftp_user
SFTP_PASS=sftp_pass
SECRET_KEY=secret_key
```

### **2️⃣ С уведомлениями:**
```bash
# Добавляем email уведомления
SMTP_SERVER=smtp.server.com
SMTP_PORT=587
SMTP_USER=notifications@server.com
SMTP_PASS=smtp_password
```

### **3️⃣ С Telegram:**
```bash
# Добавляем Telegram (опционально)
TG_BOT_TOKEN=bot_token
TG_CHAT_ID=chat_id
```

---

## ⚠️ **ВАЖНЫЕ ЗАМЕЧАНИЯ**

### **🔐 Безопасность:**
- Никогда не коммитьте `.env` файлы в Git
- Используйте App Passwords для email
- Генерируйте сложные пароли
- Регулярно ротируйте ключи

### **📧 Email провайдеры:**
- **Gmail**: требует App Password
- **Outlook**: требует App Password
- **Корпоративные**: уточните у IT-администратора

### **🚀 SFTP:**
- SSH ключи безопаснее паролей
- Проверьте права доступа к папкам
- Убедитесь в доступности сервера

### **📱 Telegram:**
- Полностью опционален
- Можно отключить в любой момент
- Удобен для оперативных уведомлений

---

## 🆘 **TROUBLESHOOTING**

### **❌ Email не читается:**
1. Проверьте `EMAIL_USER` и `EMAIL_PASS`
2. Убедитесь в использовании App Password
3. Проверьте настройки IMAP сервера

### **❌ Уведомления не отправляются:**
1. Проверьте SMTP настройки
2. Убедитесь в правильности получателей
3. Проверьте сетевую доступность

### **❌ SFTP не работает:**
1. Проверьте доступность хоста
2. Убедитесь в правильности учетных данных
3. Проверьте права доступа к папкам

### **❌ Telegram не работает:**
1. Проверьте токен бота
2. Убедитесь в правильности chat_id
3. Проверьте `enabled: true` в конфиге

Используйте тестовые скрипты для диагностики каждого компонента отдельно!
