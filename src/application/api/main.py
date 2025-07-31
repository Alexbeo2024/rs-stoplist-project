import os
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Response, status

from src.application.container import Container
from src.application.schedulers.main_scheduler import setup_scheduler, shutdown_scheduler
from src.infrastructure.logging.logger import setup_logging, get_logger

container = Container()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    # Получаем конфигурацию и инициализируем логгирование
    config = container.config()
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

@app.get("/health/ready", tags=["Health Check"])
async def ready_check():
    """Проверка готовности сервиса (проверка зависимостей)."""
    logger = get_logger(__name__)
    logger.debug("Health ready check requested")

    try:
        health_service = await container.health_check_service()
        health_result = await health_service.check_overall_health()

        if health_result["status"] == "healthy":
            logger.debug("All dependencies are healthy")
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        else:
            logger.warning(f"Health check failed: {health_result}")
            return Response(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=f"Service dependencies are unhealthy: {health_result.get('error', 'Unknown error')}",
                media_type="text/plain"
            )
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return Response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=f"Health check failed: {str(e)}",
            media_type="text/plain"
                 )

@app.get("/health/detailed", tags=["Health Check"])
async def detailed_health_check():
    """Детальная проверка состояния всех зависимостей с подробной информацией."""
    logger = get_logger(__name__)
    logger.debug("Detailed health check requested")

    try:
        health_service = await container.health_check_service()
        health_result = await health_service.check_overall_health()

        # Возвращаем полную информацию независимо от статуса
        if health_result["status"] == "healthy":
            return Response(
                status_code=status.HTTP_200_OK,
                content=health_result,
                media_type="application/json"
            )
        else:
            return Response(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=health_result,
                media_type="application/json"
            )
    except Exception as e:
        logger.error(f"Detailed health check error: {e}", exc_info=True)
        error_result = {
            "status": "unhealthy",
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat()
        }
        return Response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_result,
            media_type="application/json"
        )

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Метрики для Prometheus в стандартном формате."""
    from src.infrastructure.monitoring.metrics import metrics as prometheus_metrics

    logger = get_logger(__name__)
    logger.debug("Metrics endpoint accessed")

    try:
        # Получаем метрики в формате Prometheus
        metrics_data = prometheus_metrics.get_metrics()

        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Error generating metrics: {e}", exc_info=True)
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=f"Error generating metrics: {str(e)}",
            media_type="text/plain"
        )
