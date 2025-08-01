# 🚀 **РУКОВОДСТВО ПО РАЗВЕРТЫВАНИЮ**

*Автоматизированная система обработки Excel-файлов из email вложений*

---

## 📋 **КРАТКИЙ ОБЗОР**

Эта система автоматически:
1. **Мониторит почту** → Ищет Excel вложения (.xlsx)
2. **Конвертирует** → Excel в CSV (UTF-8 BOM)
3. **Загружает** → CSV файлы на SFTP сервер
4. **Уведомляет** → Email + Telegram (опционально)
5. **Логирует** → Полный аудит в PostgreSQL

---

## 🎯 **БЫСТРЫЙ СТАРТ (5 минут)**

### **1️⃣ Клонирование репозитория:**
```bash
git clone https://github.com/Alexbeo2024/rs-stoplist-project.git
cd rs-stoplist-project
```

### **2️⃣ Копирование конфигурации:**
```bash
# Копируем пример переменных окружения
cp env.example .env
```

### **3️⃣ Настройка основных переменных:**
Откройте `.env` и укажите:
```bash
# ===== ОБЯЗАТЕЛЬНЫЕ НАСТРОЙКИ =====

# Email для чтения файлов (Jugoexsim)
EMAIL_USER=aak@jugoexsim.rs
EMAIL_PASS=your_app_password_here

# SFTP для загрузки файлов
SFTP_HOST=your-sftp-server.com
SFTP_USER=your-sftp-user
SFTP_PASS=your-sftp-password

# База данных (можно оставить как есть для тестирования)
POSTGRES_HOST=db
POSTGRES_USER=emailprocessor
POSTGRES_PASSWORD=secure_password_123
POSTGRES_DB=email_processor_db
```

### **4️⃣ Запуск:**
```bash
docker-compose up -d
```

### **5️⃣ Проверка:**
```bash
# Статус контейнеров
docker-compose ps

# Логи приложения
docker-compose logs app

# Health check
curl http://localhost:8000/health/detailed
```

---

## 🔧 **ДЕТАЛЬНАЯ НАСТРОЙКА**

### **📧 Настройка Email (Jugoexsim)**

Ваша корпоративная почта уже протестирована! Используйте:

```bash
# В .env файле
EMAIL_USER=aak@jugoexsim.rs
EMAIL_PASS=your_actual_password

# Дополнительные настройки в config/config.test.yaml
email:
  server: "imap.gmail.com"        # Или mail.jugoexsim.rs
  port: 993
  username: "${EMAIL_USER}"
  password: "${EMAIL_PASS}"
  allowed_senders:
    - "reports@jugoexsim.rs"      # Добавьте нужных отправителей
    - "data@jugoexsim.rs"
```

### **📤 Настройка SFTP**

```bash
# В .env файле (выберите один из вариантов)

# Вариант 1: Аутентификация по паролю
SFTP_HOST=sftp.company.com
SFTP_USER=excel_processor
SFTP_PASS=your_password

# Вариант 2: Аутентификация по SSH ключу
SFTP_HOST=sftp.company.com
SFTP_USER=excel_processor
SFTP_KEY_PATH=/path/to/private_key
```

**Тестирование SFTP:**
```bash
python3 test_sftp_connection.py
```

### **📱 Настройка Telegram (ОПЦИОНАЛЬНО)**

**Включить Telegram:**
1. Создайте бота: [@BotFather](https://t.me/BotFather) → `/newbot`
2. Получите токен бота
3. Добавьте бота в группу/канал
4. Получите chat_id: [@userinfobot](https://t.me/userinfobot)

```bash
# В .env файле
TG_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyZ
TG_CHAT_ID=-1001234567890

# В config/config.test.yaml
notifications:
  telegram:
    bot_token: "${TG_BOT_TOKEN}"
    chat_id: "${TG_CHAT_ID}"
    enabled: true                 # ← Включить
```

**Отключить Telegram:**
```yaml
# В config/config.test.yaml
notifications:
  telegram:
    enabled: false                # ← Отключить
```

### **📊 Настройка уведомлений**

```bash
# Email уведомления (всегда включены)
SMTP_SERVER=smtp.jugoexsim.rs
SMTP_PORT=465
SMTP_USER=notifications@jugoexsim.rs
SMTP_PASS=smtp_password

# В config/config.test.yaml
notifications:
  email:
    smtp_server: "${SMTP_SERVER}"
    recipients:
      - "admin@jugoexsim.rs"      # Кто получает уведомления
      - "ops@jugoexsim.rs"
```

---

## 🐳 **ВАРИАНТЫ РАЗВЕРТЫВАНИЯ**

### **🟢 Вариант 1: Локальное развертывание (Рекомендуется)**

```bash
# Клонирование
git clone https://github.com/Alexbeo2024/rs-stoplist-project.git
cd rs-stoplist-project

# Настройка
cp env.example .env
nano .env  # Отредактируйте переменные

# Запуск
docker-compose up -d

# Проверка
curl http://localhost:8000/health/detailed
```

### **🟡 Вариант 2: GitHub Codespaces**

1. Перейдите на: https://github.com/Alexbeo2024/rs-stoplist-project
2. Нажмите: **Code** → **Codespaces** → **Create codespace**
3. Дождитесь инициализации (2-3 минуты)
4. В терминале:
   ```bash
   cp env.example .env
   nano .env  # Настройте переменные
   docker-compose up -d
   ```

### **🔵 Вариант 3: Сервер/VPS**

```bash
# Подключение к серверу
ssh user@your-server.com

# Установка Docker (если нужно)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Клонирование и запуск
git clone https://github.com/Alexbeo2024/rs-stoplist-project.git
cd rs-stoplist-project
cp env.example .env
nano .env  # Настройка
docker-compose up -d
```

---

## 🔍 **ТЕСТИРОВАНИЕ КОМПОНЕНТОВ**

### **📧 Тест Email (Jugoexsim)**
```bash
python3 test_jugoexsim_email.py
```
**Ожидаемый результат:**
```
✅ SMTP SSL: УСПЕШНО
✅ IMAP: УСПЕШНО
✅ Send Email: УСПЕШНО
```

### **📁 Тест SFTP**
```bash
python3 test_sftp_connection.py
```
**Интерактивный ввод:**
- Хост SFTP сервера
- Имя пользователя
- Пароль или SSH ключ
- Удаленная папка

### **🧪 Тест приложения**
```bash
python3 quick_test_jugoexsim.py
```
**Проверяет:**
- Docker контейнеры
- Health endpoints
- Database connectivity
- Email конфигурацию

### **🌐 Web интерфейс**
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health/detailed
- **Metrics**: http://localhost:8000/metrics

---

## 📊 **МОНИТОРИНГ И ЛОГИ**

### **📈 Мониторинг**
```bash
# Статус контейнеров
docker-compose ps

# Использование ресурсов
docker stats

# Health check API
curl http://localhost:8000/health/detailed | jq
```

### **📝 Логи**
```bash
# Логи приложения
docker-compose logs app

# Логи в реальном времени
docker-compose logs -f app

# Логи базы данных
docker-compose logs db

# Все логи
docker-compose logs
```

### **📊 Метрики (Prometheus)**
```bash
# Prometheus метрики
curl http://localhost:8000/metrics

# Примеры метрик:
# - emails_processed_total
# - files_converted_total
# - sftp_uploads_total
# - processing_duration_seconds
```

---

## ⚙️ **КОНФИГУРАЦИЯ**

### **🔧 Основные настройки**

**Файл:** `config/config.test.yaml`
```yaml
# Интервал проверки почты
scheduler:
  interval_hours: 1             # Каждый час

# Максимальный размер файла
file_processing:
  max_file_size_mb: 50

# Таймаут SFTP
sftp:
  timeout: 30
  max_retries: 3
```

### **📁 Структура файлов**
```
rs-stoplist-project/
├── 📁 config/                  # Конфигурация
│   ├── config.test.yaml        # Основные настройки
│   └── logging.yaml            # Настройки логирования
├── 📁 src/                     # Исходный код
│   ├── application/            # API и обработчики
│   ├── domain/                 # Бизнес-логика
│   └── infrastructure/         # Внешние сервисы
├── 📁 docs/                    # Документация
│   ├── ENVIRONMENT_VARIABLES.md
│   ├── BUSINESS_PROCESS.md
│   └── user_guide.md
├── 📁 tests/                   # Тесты
├── .env                        # Переменные окружения
├── docker-compose.yml          # Docker конфигурация
└── requirements.txt            # Python зависимости
```

---

## 🚨 **TROUBLESHOOTING**

### **❌ Проблема: Контейнеры не запускаются**
```bash
# Проверка статуса
docker-compose ps

# Проверка логов
docker-compose logs

# Пересборка образов
docker-compose build --no-cache
docker-compose up -d
```

### **❌ Проблема: Email не читается**
```bash
# Тест подключения
python3 test_jugoexsim_email.py

# Проверьте:
# 1. EMAIL_USER и EMAIL_PASS в .env
# 2. App Password (не основной пароль)
# 3. Доступность mail.jugoexsim.rs
```

### **❌ Проблема: SFTP не работает**
```bash
# Тест SFTP
python3 test_sftp_connection.py

# Проверьте:
# 1. Доступность SFTP сервера
# 2. Правильность учетных данных
# 3. Права доступа к папкам
```

### **❌ Проблема: База данных недоступна**
```bash
# Перезапуск БД
docker-compose restart db

# Проверка подключения
docker-compose exec db psql -U emailprocessor -d email_processor_db -c "\dt"
```

### **❌ Проблема: Telegram не работает**
```bash
# Проверьте в .env:
echo $TG_BOT_TOKEN
echo $TG_CHAT_ID

# Проверьте в config/config.test.yaml:
# enabled: true

# Тест бота:
curl -X GET "https://api.telegram.org/bot${TG_BOT_TOKEN}/getMe"
```

---

## 🎯 **PRODUCTION DEPLOYMENT**

### **🔒 Безопасность**
1. **Смените пароли** во всех сервисах
2. **Используйте SSH ключи** для SFTP
3. **Настройте firewall** (только нужные порты)
4. **Включите HTTPS** для API
5. **Регулярно обновляйте** зависимости

### **📈 Масштабирование**
```yaml
# docker-compose.prod.yml
app:
  deploy:
    replicas: 3
    resources:
      limits:
        cpus: '2'
        memory: 1G
```

### **💾 Бэкапы**
```bash
# Бэкап БД
docker-compose exec db pg_dump -U emailprocessor email_processor_db > backup.sql

# Бэкап конфигурации
tar -czf config_backup.tar.gz config/ .env
```

---

## 📞 **ПОДДЕРЖКА**

### **📋 Checklist запуска**
- [ ] Репозиторий склонирован
- [ ] .env файл настроен
- [ ] Email протестирован
- [ ] SFTP протестирован
- [ ] Docker контейнеры запущены
- [ ] Health checks проходят
- [ ] Уведомления работают

### **🔗 Полезные ссылки**
- **GitHub**: https://github.com/Alexbeo2024/rs-stoplist-project
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health/detailed
- **Metrics**: http://localhost:8000/metrics

### **📧 Контакты**
При возникновении проблем:
1. Проверьте логи: `docker-compose logs app`
2. Запустите тесты: `python3 quick_test_jugoexsim.py`
3. Обратитесь к документации в папке `docs/`

---

## 🎉 **ГОТОВО К РАБОТЕ!**

После успешного развертывания система будет:
- ✅ **Каждый час** проверять почту aak@jugoexsim.rs
- ✅ **Автоматически** конвертировать Excel → CSV
- ✅ **Безопасно** загружать файлы на SFTP
- ✅ **Отправлять** уведомления о статусе
- ✅ **Логировать** все операции для аудита

**Добро пожаловать в мир автоматизированной обработки данных!** 🚀
