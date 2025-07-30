# =====================================
# 1. Импорт библиотек
# =====================================
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response, status

from src.application.container import Container
from src.application.schedulers.main_scheduler import setup_scheduler, shutdown_scheduler

# =====================================
# 2. DI контейнер и жизненный цикл
# =====================================
container = Container()

# Подключаем контейнер к модулям
# container.wire(modules=[__name__, "src.application.handlers.main_handler"]) # Пример, если бы эндпоинты были здесь

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом приложения.
    Запускает и останавливает планировщик.
    """
    print("Application startup...")
    setup_scheduler()
    yield
    print("Application shutdown...")
    shutdown_scheduler()

# =====================================
# 3. Инициализация приложения
# =====================================
app = FastAPI(
    title="Email & SFTP Processor",
    description="Автоматизированная система для обработки Excel-файлов из email и отправки на SFTP.",
    version="0.1.0",
    lifespan=lifespan
)

# =====================================
# 4. Health Checks
# =====================================

@app.get("/", tags=["Health Check"])
async def root():
    """
    Корневой эндпоинт для базовой проверки доступности.
    """
    return {"message": "Service is running, scheduler is active."}

@app.get("/health/live", status_code=status.HTTP_204_NO_CONTENT, tags=["Health Check"])
async def live_check():
    """
    Проверка живоспособности сервиса (Liveness probe).
    """
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/health/ready", status_code=status.HTTP_204_NO_CONTENT, tags=["Health Check"])
async def ready_check():
    """
    Проверка готовности сервиса к обработке запросов.
    """
    # TODO: Добавить проверку зависимостей (БД, SFTP и т.д.)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# =====================================
# 5. Prometheus Metrics (Placeholder)
# =====================================

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """
    Эндпоинт для сбора метрик в формате Prometheus.
    """
    # TODO: Интегрировать Prometheus client library
    return Response(content="# Metrics placeholder", media_type="text/plain")
