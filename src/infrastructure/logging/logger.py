# =====================================
# 1. Импорт библиотек
# =====================================
import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import Dict, Any

import yaml

from src.config import LoggingConfig

# =====================================
# 2. Модуль настройки логгирования
# =====================================

_logging_initialized = False

def setup_logging(logging_config: LoggingConfig, project_root: str) -> None:
    """
    Настраивает систему логгирования приложения.

    Args:
        logging_config: Конфигурация логгирования из AppConfig
        project_root: Корневая директория проекта
    """
    global _logging_initialized

    if _logging_initialized:
        return

    # Строим путь к файлу конфигурации логгирования
    config_path = os.path.join(project_root, logging_config.config_file)

    if not os.path.exists(config_path):
        # Fallback к базовой конфигурации, если файл не найден
        _setup_basic_logging(logging_config.log_level)
        return

    # Загружаем конфигурацию из YAML
    with open(config_path, 'r', encoding='utf-8') as f:
        config_dict = yaml.safe_load(f)

    # Модифицируем конфигурацию в зависимости от настроек
    _modify_logging_config(config_dict, logging_config, project_root)

    # Применяем конфигурацию
    logging.config.dictConfig(config_dict)

    _logging_initialized = True

    # Логгируем факт инициализации
    logger = logging.getLogger(__name__)
    logger.info(f"Logging system initialized. Level: {logging_config.log_level}, File logging: {logging_config.log_to_file}")


def _modify_logging_config(config_dict: Dict[str, Any], logging_config: LoggingConfig, project_root: str) -> None:
    """
    Модифицирует словарь конфигурации логгирования в зависимости от настроек приложения.
    """
    # Устанавливаем уровень логгирования
    if 'loggers' in config_dict and 'src' in config_dict['loggers']:
        config_dict['loggers']['src']['level'] = logging_config.log_level.upper()

    # Если логгирование в файл отключено, убираем файловый handler
    if not logging_config.log_to_file:
        if 'loggers' in config_dict and 'src' in config_dict['loggers']:
            handlers = config_dict['loggers']['src'].get('handlers', [])
            if 'file' in handlers:
                handlers.remove('file')
                config_dict['loggers']['src']['handlers'] = handlers
    else:
        # Создаем директорию для логов, если она не существует
        log_dir = os.path.join(project_root, 'logs')
        Path(log_dir).mkdir(exist_ok=True)

        # Обновляем путь к файлу логов
        if 'handlers' in config_dict and 'file' in config_dict['handlers']:
            config_dict['handlers']['file']['filename'] = os.path.join(log_dir, 'app.log')


def _setup_basic_logging(log_level: str) -> None:
    """
    Настраивает базовое логгирование, если конфигурационный файл не найден.
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )


def get_logger(name: str) -> logging.Logger:
    """
    Возвращает логгер с указанным именем.

    Args:
        name: Имя логгера (обычно __name__ модуля)

    Returns:
        Настроенный логгер
    """
    return logging.getLogger(name)
