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

class DatabaseConfig(BaseSettings):
    host: str
    port: int
    user: str
    password: str
    name: str

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
    database: DatabaseConfig
    sftp: SftpConfig
    notifications: NotificationsConfig
    scheduler: SchedulerConfig

# =====================================
# 3. Функция загрузки конфигурации
# =====================================

@lru_cache()
def get_config() -> AppConfig:
    # Определяем корень проекта как родителя директории 'src'
    # __file__ -> /path/to/project/src/config/__init__.py
    # os.path.dirname(__file__) -> /path/to/project/src/config
    # os.path.dirname(os.path.dirname(__file__)) -> /path/to/project/src
    # os.path.dirname(os.path.dirname(os.path.dirname(__file__))) -> /path/to/project
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(project_root, "config", "config.yaml")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    # Загружаем переменные окружения для подстановки
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(config_path), '.env')
    load_dotenv(dotenv_path=env_path)

    # Рекурсивная подстановка переменных
    def substitute_env_vars(data):
        if isinstance(data, dict):
            return {k: substitute_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [substitute_env_vars(i) for i in data]
        elif isinstance(data, str) and data.startswith('${') and data.endswith('}'):
            var_name = data[2:-1]
            return os.getenv(var_name, data) # Возвращаем исходную строку, если переменная не найдена
        return data

    substituted_config = substitute_env_vars(config_data)

    return AppConfig(**substituted_config)

# config = get_config() # <--- УДАЛЯЕМ ЭТУ СТРОКУ
