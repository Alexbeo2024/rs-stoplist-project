# 📧 **НАСТРОЙКА EMAIL ДЛЯ ТЕСТИРОВАНИЯ**

## 🚀 **Быстрая настройка (2 способа)**

### **⚡ Способ 1: Интерактивный скрипт (РЕКОМЕНДУЕМЫЙ)**

```bash
python3 setup_email.py
```

Скрипт автоматически:
- ✅ Определит ваш email провайдер
- ✅ Настроит SMTP/IMAP параметры
- ✅ Подскажет как создать App Password (если нужно)
- ✅ Сохранит конфигурацию в `.env`
- ✅ Предложит протестировать настройки

### **🛠️ Способ 2: Ручная настройка**

Отредактируйте `.env` файл:

```bash
# Gmail (требует App Password)
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password-16-chars
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993

# Outlook/Hotmail
EMAIL_USER=your-email@outlook.com
EMAIL_PASS=your-regular-password
SMTP_SERVER=smtp.live.com
SMTP_PORT=587
IMAP_SERVER=imap.live.com
IMAP_PORT=993

# Yandex (требует App Password)
EMAIL_USER=your-email@yandex.ru
EMAIL_PASS=your-app-password
SMTP_SERVER=smtp.yandex.ru
SMTP_PORT=587
IMAP_SERVER=imap.yandex.ru
IMAP_PORT=993
```

---

## 🔐 **App Password для Gmail (ОБЯЗАТЕЛЬНО!)**

### **Пошаговая инструкция:**
1. **Зайдите в Google Account**: [myaccount.google.com](https://myaccount.google.com)
2. **Security** → **2-Step Verification** → Включите 2FA
3. **App passwords** → **Generate app password**
4. **Выберите app**: Mail
5. **Выберите device**: Other (custom name) → "Excel Processor"
6. **Скопируйте 16-символьный пароль** (вида: `abcd efgh ijkl mnop`)
7. **Используйте этот пароль** в `EMAIL_PASS`

🔗 **Прямая ссылка**: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

---

## 🧪 **Тестирование настроек**

### **Comprehensive тест:**
```bash
python3 test_email_smtp.py
```

**Что проверяется:**
- ✅ SMTP подключение и аутентификация
- ✅ IMAP подключение и доступ к папкам
- ✅ Отправка тестового email самому себе
- ✅ Анализ email провайдера
- ✅ Генерация рекомендаций

### **Быстрый тест:**
```bash
# Проверка приложения
docker-compose up -d
python3 quick_test.py
```

---

## 🏢 **Корпоративная почта**

Для корпоративной почты (Exchange, custom SMTP):

1. **Узнайте у администратора:**
   - SMTP сервер и порт
   - IMAP сервер и порт
   - Требования по безопасности

2. **Добавьте в `.env`:**
   ```bash
   EMAIL_USER=user@company.com
   EMAIL_PASS=your-corporate-password
   SMTP_SERVER=mail.company.com
   SMTP_PORT=587
   IMAP_SERVER=mail.company.com
   IMAP_PORT=993
   ```

3. **Возможные проблемы:**
   - Firewall блокирует порты
   - Требуется VPN подключение
   - Нужны специальные настройки безопасности

---

## 🆘 **Troubleshooting**

### **SMTP Authentication Error:**
- ❌ **Проблема**: `Username and Password not accepted`
- ✅ **Решение**:
  - Gmail: Используйте App Password вместо обычного
  - Outlook: Проверьте пароль и включите IMAP
  - Убедитесь что нет опечаток в email/пароле

### **Connection Timeout:**
- ❌ **Проблема**: Не удается подключиться к серверу
- ✅ **Решение**:
  - Проверьте интернет соединение
  - Убедитесь что firewall не блокирует порты 587/993
  - Попробуйте с другой сети

### **IMAP Not Enabled:**
- ❌ **Проблема**: IMAP access denied
- ✅ **Решение**:
  - Gmail: IMAP включен по умолчанию
  - Outlook: Settings → Sync email → Enable IMAP
  - Yahoo: Settings → More Settings → Mailboxes → Enable IMAP

---

## 📊 **Что дальше после настройки:**

### **1. GitHub Secrets (для CI/CD):**
Добавьте в GitHub Repository Settings:
```
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password
```

### **2. Production конфигурация:**
```bash
# Копируйте в production .env
cp .env .env.production
# Отредактируйте для production email аккаунта
```

### **3. Запуск системы:**
```bash
# Локально
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🎯 **Результат успешной настройки:**

При запуске `python3 test_email_smtp.py` вы должны увидеть:

```
✅ Email Provider Analysis: ИНФОРМАЦИЯ
✅ SMTP Connection: УСПЕШНО
✅ IMAP Connection: УСПЕШНО
✅ Send Email: УСПЕШНО
📧 Test email отправлен на ваш адрес!
```

**🎉 После этого ваша система готова к обработке Excel-файлов из email!**
