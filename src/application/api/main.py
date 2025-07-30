import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response, status

from src.application.container import Container
from src.application.schedulers.main_scheduler import setup_scheduler, shutdown_scheduler
from src.infrastructure.logging.logger import setup_logging, get_logger

container = Container()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    # Получаем конфигурацию и инициализируем логгирование
    config = await container.config()
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    setup_logging(config.logging, project_root)

    logger = get_logger(__name__)
    logger.info("Application startup...")

    # Запускаем планировщик
    setup_scheduler()
    logger.info("Scheduler started")

    yield

    logger.info("Application shutdown...")
    shutdown_scheduler()
    logger.info("Scheduler stopped")

app = FastAPI(
    title="Email & SFTP Processor",
    description="Автоматизированная система для обработки Excel-файлов из email и отправки на SFTP.",
    version="0.1.0",
    lifespan=lifespan
)

@app.get("/", tags=["Health Check"])
async def root():
    logger = get_logger(__name__)
    logger.info("Root endpoint accessed")
    return {"message": "Service is running, scheduler is active."}

@app.get("/health/live", status_code=status.HTTP_204_NO_CONTENT, tags=["Health Check"])
async def live_check():
    """Проверка живости сервиса (простая проверка)."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/health/ready", status_code=status.HTTP_204_NO_CONTENT, tags=["Health Check"])
async def ready_check():
    """Проверка готовности сервиса (проверка зависимостей)."""
    logger = get_logger(__name__)
    logger.debug("Health ready check requested")
    # TODO: Добавить проверку зависимостей (БД, SFTP и т.д.)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Метрики для Prometheus."""
    logger = get_logger(__name__)
    logger.debug("Metrics endpoint accessed")
    # TODO: Интегрировать Prometheus client library
    return Response(content="# Metrics placeholder", media_type="text/plain")
