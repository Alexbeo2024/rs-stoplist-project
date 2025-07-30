# =====================================
# 1. Импорт библиотек
# =====================================
from fastapi import FastAPI, Response, status

# =====================================
# 2. Инициализация приложения
# =====================================
app = FastAPI(
    title="Email & SFTP Processor",
    description="Автоматизированная система для обработки Excel-файлов из email и отправки на SFTP.",
    version="0.1.0",
)

# =====================================
# 3. Health Checks
# =====================================

@app.get("/", tags=["Health Check"])
async def root():
    """
    Корневой эндпоинт для базовой проверки доступности.
    """
    return {"message": "Service is running"}

@app.get("/health/live", status_code=status.HTTP_204_NO_CONTENT, tags=["Health Check"])
async def live_check():
    """
    Проверка живоспособности сервиса (Liveness probe).
    Отвечает 204 No Content, если приложение запущено.
    """
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/health/ready", status_code=status.HTTP_204_NO_CONTENT, tags=["Health Check"])
async def ready_check():
    """
    Проверка готовности сервиса к обработке запросов (Readiness probe).
    В будущем здесь будет проверка подключения к БД, SFTP и т.д.
    """
    # TODO: Добавить проверку зависимостей (БД, SFTP и т.д.)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# =====================================
# 4. Prometheus Metrics (Placeholder)
# =====================================

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """
    Эндпоинт для сбора метрик в формате Prometheus.
    Будет реализован с использованием соответствующей библиотеки.
    """
    # TODO: Интегрировать Prometheus client library
    return Response(content="# Metrics placeholder", media_type="text/plain")
