# 🚀 **БЫСТРОЕ РАЗВЕРТЫВАНИЕ НА GITHUB**

## 📋 **3 способа развертывания**

### **🔥 Способ 1: Автоматический (РЕКОМЕНДУЕМЫЙ)**

```bash
# Одна команда - все готово!
./deploy.sh username/rs-stoplist-project
```

### **🛠️ Способ 2: Ручной (пошагово)**

```bash
# 1. Создайте репозиторий на GitHub
gh repo create rs-stoplist-project --public

# 2. Настройте git
git remote add origin https://github.com/USERNAME/rs-stoplist-project.git
git branch -M main
git push -u origin main

# 3. Создайте первый релиз
git tag v1.0.0
git push origin v1.0.0
```

### **🌐 Способ 3: GitHub Codespaces**

1. Зайдите на **GitHub.com**
2. Нажмите **"Code"** → **"Create codespace"**
3. Автоматически запустится dev environment
4. Приложение будет доступно на порту **8000**

## ⚙️ **Обязательная настройка секретов**

В **GitHub Repository Settings** → **Secrets and variables** → **Actions** добавьте:

```bash
POSTGRES_PASSWORD=your_secure_password
EMAIL_USER=your-email@domain.com
EMAIL_PASS=your-app-password
SFTP_HOST=your-sftp-server.com
SFTP_USER=your-sftp-user
SFTP_PASS=your-sftp-password
SECRET_KEY=generate-strong-secret-key
TG_BOT_TOKEN=your-telegram-bot-token
TG_CHAT_ID=your-chat-id
```

## 🎯 **Что происходит автоматически**

✅ **CI/CD Pipeline запускается** при каждом push
✅ **Docker образы собираются** для AMD64/ARM64
✅ **Security scanning** с Bandit и Trivy
✅ **Code quality checks** с Black, Ruff, MyPy
✅ **Automated testing** с PostgreSQL
✅ **Container Registry** публикация в GHCR

## 📊 **Полезные ссылки после развертывания**

- **🔄 CI/CD Status**: `https://github.com/Alexbeo2024/rs-stoplist-project/actions`
- **🐳 Docker Images**: `https://github.com/Alexbeo2024/rs-stoplist-project/pkgs/container/rs-stoplist-project`
- **🌐 Codespaces**: `https://github.com/Alexbeo2024/rs-stoplist-project/codespaces`
- **📖 API Docs**: `http://localhost:8000/docs` (в Codespace)
- **💚 Health Check**: `http://localhost:8000/health/detailed`

## 🆘 **Если что-то не работает**

1. **Проверьте секреты** в GitHub Settings
2. **Посмотрите логи** в GitHub Actions
3. **Используйте** `python3 quick_test.py` для локальной диагностики
4. **Читайте полную документацию** в [docs/deployment_guide.md](docs/deployment_guide.md)

---

## ⚡ **Одна команда для всего:**

```bash
chmod +x deploy.sh && ./deploy.sh
```

**🎉 И ваше приложение готово к production на GitHub!**
