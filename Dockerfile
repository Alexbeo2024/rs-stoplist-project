# =================================================================
# Этап 1: Builder - Установка зависимостей
# =================================================================
FROM python:3.11-slim as builder

# Устанавливаем рабочую директорию
WORKDIR /opt/app

# Устанавливаем переменные окружения для Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем poetry
# RUN pip install poetry

# Копируем файлы зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /opt/app/wheels -r requirements.txt


# =================================================================
# Этап 2: Final - Создание финального образа
# =================================================================
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /opt/app

# Копируем установленные зависимости из builder
COPY --from=builder /opt/app/wheels /wheels
COPY --from=builder /opt/app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Копируем исходный код приложения
COPY ./src /opt/app/src
COPY ./config /opt/app/config

# Указываем команду для запуска приложения
CMD ["uvicorn", "src.application.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
