# =====================================
# Email SFTP Processor - Development Tools
# =====================================
# Удобные команды для разработки и проверки качества кода

.PHONY: help install clean lint format security test coverage pre-commit docker-up docker-down

# Переменные
PYTHON := python3.11
PIP := pip
SRC_DIR := src
TEST_DIR := tests

# =====================================
# Help - показать доступные команды
# =====================================
help:
	@echo "📋 Доступные команды:"
	@echo ""
	@echo "🔧 Установка и настройка:"
	@echo "  install           Установить все зависимости"
	@echo "  install-dev       Установить зависимости для разработки"
	@echo "  clean             Очистить временные файлы"
	@echo ""
	@echo "🔍 Проверка качества кода:"
	@echo "  lint              Запустить все линтеры"
	@echo "  format            Отформатировать код"
	@echo "  security          Проверка безопасности"
	@echo "  type-check        Проверка типов"
	@echo ""
	@echo "🧪 Тестирование:"
	@echo "  test              Запустить все тесты"
	@echo "  test-unit         Запустить только unit тесты"
	@echo "  test-integration  Запустить интеграционные тесты"
	@echo "  coverage          Анализ покрытия тестами"
	@echo ""
	@echo "🔒 Pre-commit hooks:"
	@echo "  pre-commit-install Установить pre-commit hooks"
	@echo "  pre-commit-run     Запустить pre-commit на всех файлах"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  docker-up         Запустить Docker окружение"
	@echo "  docker-down       Остановить Docker окружение"
	@echo "  docker-build      Собрать Docker образ"
	@echo ""
	@echo "✅ Комплексные проверки:"
	@echo "  check-all         Запустить все проверки (lint + security + tests)"
	@echo "  ci                Имитация CI pipeline"

# =====================================
# Установка и настройка
# =====================================
install:
	$(PIP) install -r requirements.txt

install-dev: install
	$(PIP) install -e .
	$(MAKE) pre-commit-install

clean:
	@echo "🧹 Очистка временных файлов..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf build/
	rm -rf dist/
	@echo "✅ Очистка завершена"

# =====================================
# Проверка качества кода
# =====================================
lint:
	@echo "🔍 Запуск линтеров..."
	ruff check $(SRC_DIR) $(TEST_DIR)
	@echo "✅ Ruff проверка завершена"

format:
	@echo "✨ Форматирование кода..."
	black $(SRC_DIR) $(TEST_DIR)
	isort $(SRC_DIR) $(TEST_DIR)
	@echo "✅ Форматирование завершено"

security:
	@echo "🔒 Проверка безопасности..."
	bandit -r $(SRC_DIR) -c pyproject.toml -f text
	@echo "✅ Bandit проверка завершена"

type-check:
	@echo "📝 Проверка типов..."
	mypy $(SRC_DIR) --config-file pyproject.toml
	@echo "✅ MyPy проверка завершена"

# =====================================
# Тестирование
# =====================================
test:
	@echo "🧪 Запуск всех тестов..."
	pytest $(TEST_DIR) -v

test-unit:
	@echo "🧪 Запуск unit тестов..."
	pytest $(TEST_DIR) -v -m "not integration"

test-integration:
	@echo "🧪 Запуск интеграционных тестов..."
	APP_ENV=test pytest $(TEST_DIR)/integration/ -v

coverage:
	@echo "📊 Анализ покрытия тестами..."
	pytest $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing
	@echo "📋 Отчет сохранен в htmlcov/index.html"

# =====================================
# Pre-commit hooks
# =====================================
pre-commit-install:
	@echo "🔧 Установка pre-commit hooks..."
	pre-commit install
	@echo "✅ Pre-commit hooks установлены"

pre-commit-run:
	@echo "🔍 Запуск pre-commit на всех файлах..."
	pre-commit run --all-files

# =====================================
# Docker
# =====================================
docker-up:
	@echo "🐳 Запуск Docker окружения..."
	docker-compose up -d

docker-down:
	@echo "🐳 Остановка Docker окружения..."
	docker-compose down

docker-build:
	@echo "🐳 Сборка Docker образа..."
	docker-compose build

# =====================================
# Комплексные проверки
# =====================================
check-all: format lint type-check security test
	@echo "✅ Все проверки завершены успешно!"

ci: lint type-check security test-unit
	@echo "🚀 CI pipeline завершен успешно!"

# =====================================
# Вспомогательные команды
# =====================================
deps-update:
	@echo "📦 Обновление зависимостей..."
	$(PIP) list --outdated
	@echo "💡 Для обновления: pip install --upgrade <package_name>"

deps-audit:
	@echo "🔍 Аудит безопасности зависимостей..."
	pip-audit --requirement requirements.txt

# =====================================
# Разработка
# =====================================
run-dev:
	@echo "🚀 Запуск приложения в режиме разработки..."
	uvicorn src.application.api.main:app --reload --host 0.0.0.0 --port 8000

logs:
	@echo "📋 Показ логов Docker контейнеров..."
	docker-compose logs -f

# =====================================
# Мониторинг
# =====================================
metrics:
	@echo "📊 Получение метрик приложения..."
	curl -s http://localhost:8000/metrics | head -n 20

health:
	@echo "🏥 Проверка health status..."
	curl -s http://localhost:8000/health/detailed | python -m json.tool
