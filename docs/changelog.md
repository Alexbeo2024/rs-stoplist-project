## [2024-07-30] - Инициализация проекта

### ✅ Добавлено
- Создана структура каталогов проекта.
- Инициализирован Git-репозиторий.
- Созданы файлы `docs/changelog.md` и `docs/tasktracker.md`.
- Добавлен файл `.gitignore`.

## [2024-07-30] - Конфигурация и модели данных

### ✅ Добавлено
- Создан файл `config/config.yaml` с базовой конфигурацией.
- Определены Pydantic-модели `ProcessedFile` и `OperationLog` в `src/domain/models/`.
- Создан SQL-скрипт `docs/schema.sql` для определения схемы БД.

## [2024-07-30] - Настройка зависимостей и базового приложения

### ✅ Добавлено
- Создан файл `requirements.txt` с основными зависимостями.
- Создано базовое FastAPI-приложение `src/application/api/main.py` с health-check эндпоинтами.
- Реализован модуль `src/config/__init__.py` для загрузки и валидации конфигурации.

## [2024-07-30] - Инфраструктурный слой: База данных и Репозитории

### ✅ Добавлено
- Настроен модуль `src/infrastructure/storage/database.py` для асинхронной работы с БД.
- В `src/domain/repositories/__init__.py` определены абстрактные интерфейсы репозиториев.
- В `src/infrastructure/storage/repositories.py` реализованы конкретные репозитории на SQLAlchemy.

## [2024-07-30] - Настройка Docker и Docker Compose

### ✅ Добавлено
- Создан многостадийный `Dockerfile` для сборки production-образа.
- Создан файл `.dockerignore` для оптимизации контекста сборки.
- Настроен `docker-compose.yml` с сервисами приложения, PostgreSQL и Adminer.
- (Пропущено) Создание `.env.example` заблокировано, требуется ручное создание.

## [2024-07-30] - Реализация основной бизнес-логики: Сервисный слой

### ✅ Добавлено
- В `src/domain/services/` определены абстрактные интерфейсы для сервисов `IEmailReaderService`, `IFileProcessingService`, `ISftpUploadService`.
- Созданы placeholder-реализации для `EmailReaderService`, `FileProcessingService`, `SftpUploadService`.
- В `src/application/handlers/main_handler.py` реализован главный сервис-оркестратор.

## [2024-07-30] - Сборка: Dependency Injection и планировщик

### ✅ Добавлено
- В `requirements.txt` добавлены `dependency-injector` и `apscheduler`.
- В `src/application/container.py` создан DI-контейнер для управления зависимостями.
- В `src/application/schedulers/main_scheduler.py` настроен `APScheduler` для периодического запуска обработки.
- В `src/application/api/main.py` интегрирован DI-контейнер и управление жизненным циклом планировщика.
