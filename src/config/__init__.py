# =====================================
# 1. Импорт библиотек
# =====================================
import os
from functools import lru_cache
from typing import List

import yaml
from pydantic_settings import BaseSettings

# =====================================
# 2. Определение моделей конфигурации
# =====================================

class EmailConfig(BaseSettings):
    server: str
    port: int
    username: str
    password: str
    allowed_senders: List[str]

class SftpConfig(BaseSettings):
    host: str
    username: str
    key_path: str
    remote_path: str

class NotificationsConfig(BaseSettings):
    class Email(BaseSettings):
        smtp_server: str
        recipients: List[str]

    class Telegram(BaseSettings):
        bot_token: str
        chat_id: str

    email: Email
    telegram: Telegram

class SchedulerConfig(BaseSettings):
    interval_hours: int

class AppConfig(BaseSettings):
    email: EmailConfig
    sftp: SftpConfig
    notifications: NotificationsConfig
    scheduler: SchedulerConfig

# =====================================
# 3. Функция загрузки конфигурации
# =====================================

@lru_cache()
def get_config(config_path: str = "config.yaml") -> AppConfig:
    """
    Загружает конфигурацию из YAML файла и переменных окружения.

    Использует pydantic-settings для автоматического переопределения
    значений из YAML переменными окружения.

    Args:
        config_path: Путь к файлу конфигурации.

    Returns:
        Объект AppConfig с полной конфигурацией приложения.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    # Pydantic-settings автоматически подхватит переменные окружения
    # для полей, обернутых в ${...}
    return AppConfig(**config_data)

# =====================================
# 4. Экспорт инстанса конфигурации
# =====================================
config = get_config()
