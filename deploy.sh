#!/bin/bash
# =====================================
# АВТОМАТИЗИРОВАННЫЙ ДЕПЛОЙ НА GITHUB
# =====================================

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции логирования
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."

    # Проверка git
    if ! command -v git &> /dev/null; then
        log_error "Git не установлен!"
        exit 1
    fi

    # Проверка GitHub CLI (опционально)
    if ! command -v gh &> /dev/null; then
        log_warning "GitHub CLI не установлен. Репозиторий нужно будет создать вручную."
    fi

    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен!"
        exit 1
    fi

    log_success "Все зависимости проверены"
}

# Проверка работоспособности приложения
test_application() {
    log_info "Тестирование приложения локально..."

    # Запуск контейнеров
    docker-compose up -d
    sleep 10

    # Проверка health check
    if curl -f http://localhost:8000/health/live > /dev/null 2>&1; then
        log_success "Приложение работает корректно"
    else
        log_error "Приложение не отвечает на health check"
        docker-compose logs app | tail -10
        exit 1
    fi

    # Остановка контейнеров
    docker-compose down
}

# Настройка GitHub репозитория
setup_github_repo() {
    log_info "Настройка GitHub репозитория..."

    # Получение имени репозитория
    if [ -z "$1" ]; then
        read -p "Введите имя репозитория (например, username/rs-stoplist-project): " REPO_NAME
    else
        REPO_NAME=$1
    fi

    # Проверка существования репозитория
    if git remote get-url origin > /dev/null 2>&1; then
        log_warning "Git remote origin уже настроен"
        EXISTING_REMOTE=$(git remote get-url origin)
        log_info "Текущий remote: $EXISTING_REMOTE"
    else
        # Создание репозитория через GitHub CLI
        if command -v gh &> /dev/null; then
            log_info "Создание репозитория через GitHub CLI..."
            gh repo create $REPO_NAME --public --description "Автоматизированная система обработки Excel-файлов из email"
            git remote add origin https://github.com/$REPO_NAME.git
        else
            log_warning "Создайте репозиторий вручную на GitHub: https://github.com/new"
            echo "Затем добавьте remote:"
            echo "git remote add origin https://github.com/$REPO_NAME.git"
            read -p "Нажмите Enter после создания репозитория..."
        fi
    fi

    log_success "GitHub репозиторий настроен"
}

# Подготовка файлов для GitHub
prepare_github_files() {
    log_info "Подготовка файлов для GitHub..."

    # Создание .gitignore если не существует
    if [ ! -f .gitignore ]; then
        cat > .gitignore << EOF
# Environment files
.env
.env.local
.env.production

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Docker
.dockerignore

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Coverage
htmlcov/
.coverage
coverage.xml

# pytest
.pytest_cache/

# MyPy
.mypy_cache/

# Test files
test_data/
*.xlsx
*.csv
EOF
        log_success ".gitignore создан"
    fi

    # Проверка наличия необходимых файлов
    REQUIRED_FILES=(
        ".github/workflows/ci.yml"
        ".devcontainer/devcontainer.json"
        "docker-compose.prod.yml"
        "env.example"
        "docs/deployment_guide.md"
    )

    for file in "${REQUIRED_FILES[@]}"; do
        if [ ! -f "$file" ]; then
            log_warning "Файл $file не найден"
        else
            log_success "Файл $file готов"
        fi
    done
}

# Коммит и пуш изменений
commit_and_push() {
    log_info "Коммит и отправка изменений..."

    # Проверка изменений
    if [ -z "$(git status --porcelain)" ]; then
        log_warning "Нет изменений для коммита"
        return
    fi

    # Добавление всех файлов
    git add .

    # Коммит
    COMMIT_MESSAGE="feat: add comprehensive GitHub deployment configuration

- Add CI/CD pipeline with GitHub Actions
- Add Docker production configuration
- Add Codespaces development environment
- Add deployment documentation
- Add security scanning and monitoring
- Ready for production deployment"

    git commit -m "$COMMIT_MESSAGE"

    # Пуш в main ветку
    git branch -M main
    git push -u origin main

    log_success "Изменения отправлены в GitHub"
}

# Создание релиза
create_release() {
    log_info "Создание первого релиза..."

    VERSION="v1.0.0"

    # Создание тега
    git tag $VERSION
    git push origin $VERSION

    log_success "Релиз $VERSION создан"

    if command -v gh &> /dev/null; then
        gh release create $VERSION --title "Initial Production Release" --notes "
🚀 **Первый production-ready релиз**

## Что включено:
- ✅ Полная система обработки Excel файлов
- ✅ CI/CD pipeline с GitHub Actions
- ✅ Docker контейнеризация
- ✅ Health checks и мониторинг
- ✅ Security scanning
- ✅ Production-ready конфигурация

## Развертывание:
\`\`\`bash
# Клонирование
git clone https://github.com/$REPO_NAME.git
cd rs-stoplist-project

# Настройка окружения
cp env.example .env
# Отредактируйте .env файл

# Запуск
docker-compose -f docker-compose.prod.yml up -d
\`\`\`

Документация: [docs/deployment_guide.md](docs/deployment_guide.md)
"
        log_success "GitHub релиз создан"
    fi
}

# Вывод инструкций для пользователя
show_final_instructions() {
    echo ""
    echo "🎉 РАЗВЕРТЫВАНИЕ НА GITHUB ЗАВЕРШЕНО!"
    echo "=================================="
    echo ""
    echo "📋 ЧТО ДАЛЬШЕ:"
    echo ""
    echo "1. 🔐 Настройте секреты в GitHub Repository Settings:"
    echo "   https://github.com/$REPO_NAME/settings/secrets/actions"
    echo ""
    echo "   Обязательные секреты:"
    echo "   - POSTGRES_PASSWORD"
    echo "   - EMAIL_USER"
    echo "   - EMAIL_PASS"
    echo "   - SECRET_KEY"
    echo ""
    echo "2. 🚀 GitHub Actions автоматически запустится при следующем push"
    echo ""
    echo "3. 🌐 Для использования Codespaces:"
    echo "   https://github.com/$REPO_NAME/codespaces"
    echo ""
    echo "4. 📊 Мониторинг CI/CD:"
    echo "   https://github.com/$REPO_NAME/actions"
    echo ""
    echo "5. 🐳 Docker образы будут доступны в:"
    echo "   https://github.com/$REPO_NAME/pkgs/container/rs-stoplist-project"
    echo ""
    echo "📖 Полная документация: docs/deployment_guide.md"
    echo ""
}

# Основная функция
main() {
    echo "🚀 АВТОМАТИЗИРОВАННОЕ РАЗВЕРТЫВАНИЕ НА GITHUB"
    echo "============================================"
    echo ""

    # Проверка аргументов
    REPO_NAME=$1

    # Выполнение шагов
    check_dependencies
    test_application
    setup_github_repo $REPO_NAME
    prepare_github_files
    commit_and_push
    create_release
    show_final_instructions

    echo ""
    log_success "🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО УСПЕШНО!"
}

# Проверка аргументов командной строки
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Использование: $0 [repository-name]"
    echo ""
    echo "Примеры:"
    echo "  $0 username/rs-stoplist-project"
    echo "  $0  # интерактивный режим"
    echo ""
    echo "Этот скрипт:"
    echo "- Тестирует приложение локально"
    echo "- Настраивает GitHub репозиторий"
    echo "- Создает CI/CD pipeline"
    echo "- Настраивает Codespaces"
    echo "- Создает первый релиз"
    exit 0
fi

# Запуск основной функции
main $1
