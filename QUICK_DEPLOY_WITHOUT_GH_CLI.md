# 🚀 **РАЗВЕРТЫВАНИЕ БЕЗ GITHUB CLI**

## ⚠️ **Если у вас нет GitHub CLI или проблемы с аутентификацией**

### **📝 Шаг 1: Создайте репозиторий вручную**

1. Зайдите на [github.com/new](https://github.com/new)
2. Введите название: `rs-stoplist-project`
3. Выберите **Public** репозиторий
4. Нажмите **"Create repository"**

### **🔗 Шаг 2: Подключите локальный репозиторий**

```bash
# Если еще не инициализирован git
git init

# Добавьте все файлы
git add .

# Сделайте первый коммит
git commit -m "feat: initial commit - production-ready Excel processing system"

# Добавьте GitHub remote (замените USERNAME на ваш GitHub username)
git remote add origin https://github.com/USERNAME/rs-stoplist-project.git

# Установите main как основную ветку
git branch -M main

# Отправьте код на GitHub
git push -u origin main
```

### **🏷️ Шаг 3: Создайте первый релиз**

```bash
# Создайте тег
git tag v1.0.0

# Отправьте тег на GitHub
git push origin v1.0.0
```

### **⚙️ Шаг 4: Настройте секреты в GitHub**

1. Зайдите в настройки репозитория: `https://github.com/USERNAME/rs-stoplist-project/settings`
2. Перейдите в **"Secrets and variables"** → **"Actions"**
3. Нажмите **"New repository secret"** и добавьте каждый секрет:

```bash
# Обязательные секреты:
POSTGRES_PASSWORD=your_secure_password_123
EMAIL_USER=your-email@domain.com
EMAIL_PASS=your-email-app-password
SFTP_HOST=your-sftp-server.com
SFTP_USER=your-sftp-user
SFTP_PASS=your-sftp-password
SECRET_KEY=generate-strong-secret-key-32-chars
TG_BOT_TOKEN=your-telegram-bot-token
TG_CHAT_ID=your-telegram-chat-id

# Опциональные для advanced features:
REDIS_PASSWORD=your-redis-password
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
```

### **🚀 Шаг 5: Проверьте автоматический CI/CD**

1. **GitHub Actions запустится автоматически** после push
2. Проверьте статус: `https://github.com/USERNAME/rs-stoplist-project/actions`
3. Если все зеленое ✅ - ваше приложение готово!

### **🌐 Шаг 6: Запустите Codespace (опционально)**

1. Зайдите в репозиторий на GitHub
2. Нажмите **"Code"** → **"Codespaces"** → **"Create codespace"**
3. Дождитесь инициализации (2-3 минуты)
4. Приложение автоматически запустится на порту **8000**

### **🧪 Шаг 7: Тестирование**

#### **В Codespace:**
```bash
# Приложение уже запущено, просто проверьте
curl http://localhost:8000/health/detailed
```

#### **На локальной машине:**
```bash
# Запустите контейнеры
docker-compose up -d

# Проверьте работоспособность
python3 quick_test.py
```

### **📊 Полезные ссылки после настройки:**

- **🔄 CI/CD Pipeline**: `https://github.com/USERNAME/rs-stoplist-project/actions`
- **🐳 Docker Images**: `https://github.com/USERNAME/rs-stoplist-project/pkgs/container/rs-stoplist-project`
- **🌐 Codespaces**: `https://github.com/USERNAME/rs-stoplist-project/codespaces`
- **📖 Issues & Support**: `https://github.com/USERNAME/rs-stoplist-project/issues`

### **🆘 Troubleshooting:**

#### **CI/CD не запускается:**
- Проверьте, что файл `.github/workflows/ci.yml` есть в репозитории
- Убедитесь, что в Settings → Actions включены workflows

#### **Secrets не работают:**
- Имена секретов должны точно совпадать (CAPS_LOCK)
- Не должно быть пробелов в начале/конце значений

#### **Docker build fails:**
- Проверьте логи в GitHub Actions
- Локально выполните: `docker build -t test .`

---

## ⚡ **Быстрый чек-лист:**

- [ ] Создал репозиторий на GitHub
- [ ] Сделал `git push -u origin main`
- [ ] Создал тег `v1.0.0` и запушил его
- [ ] Настроил все секреты в GitHub Settings
- [ ] Проверил GitHub Actions (должен быть зеленый ✅)
- [ ] Создал Codespace для разработки
- [ ] Протестировал health endpoints

**🎉 Готово! Ваше приложение теперь на GitHub с полной автоматизацией!**
