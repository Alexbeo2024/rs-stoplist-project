# =====================================
# 1. Импорт библиотек
# =====================================
from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.config import get_config
from src.infrastructure.email.email_reader import EmailReaderService
from src.infrastructure.storage.file_processor import FileProcessingService
from src.infrastructure.sftp.sftp_uploader import SftpUploadService
from src.infrastructure.storage.repositories import ProcessedFileRepository, OperationLogRepository
from src.infrastructure.notifications.email_sender import EmailSender
from src.infrastructure.notifications.telegram_sender import TelegramSender
from src.domain.repositories import IProcessedFileRepository, IOperationLogRepository
from src.domain.services import IEmailReaderService, IFileProcessingService, ISftpUploadService
from src.domain.services.notifications import INotificationService
from src.application.handlers.main_handler import MainHandler
from src.application.api.health_checks import HealthCheckService

# =====================================
# 2. Определение DI контейнера
# =====================================

class Container(containers.DeclarativeContainer):
    """
    Главный DI контейнер приложения.
    """
    # --- Конфигурация ---
    config = providers.Singleton(get_config) # Создаем синглтон конфигурации

    # --- Подключения ---
    db_engine = providers.Singleton(
        create_async_engine,
        url=providers.Callable(
            lambda user, password, host, port, name: f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}",
            user=config.provided.database.user,
            password=config.provided.database.password,
            host=config.provided.database.host,
            port=config.provided.database.port,
            name=config.provided.database.name,
        )
    )

    db_session_factory = providers.Singleton(
        sessionmaker,
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # --- Репозитории ---
    processed_file_repo: providers.Factory[IProcessedFileRepository] = providers.Factory(
        ProcessedFileRepository,
        session=db_session_factory, # Исправлено с session_factory на session
    )

    operation_log_repo: providers.Factory[IOperationLogRepository] = providers.Factory(
        OperationLogRepository,
        session=db_session_factory, # Исправлено с session_factory на session
    )

    # --- Сервисы уведомлений (условная регистрация) ---

    # Email sender (всегда доступен)
    email_sender: providers.Factory[INotificationService] = providers.Factory(
        EmailSender,
        config=config.provided.notifications.email,
    )

    # Telegram sender (опциональный)
    telegram_sender: providers.Factory[INotificationService] = providers.Factory(
        TelegramSender,
        config=config.provided.notifications.telegram,
    )

    # Список сервисов уведомлений (динамически формируется)
    notification_services = providers.List(
        email_sender,
        # telegram_sender добавляется условно в main_handler
    )

    # --- Основные сервисы ---
    email_service: providers.Factory[IEmailReaderService] = providers.Factory(
        EmailReaderService,
        config=config.provided.email,
    )

    file_service: providers.Factory[IFileProcessingService] = providers.Factory(
        FileProcessingService,
    )

    sftp_service: providers.Factory[ISftpUploadService] = providers.Factory(
        SftpUploadService,
        config=config.provided.sftp,
    )

    # --- Главный обработчик ---
    async def main_handler(self) -> MainHandler:
        """
        Создает MainHandler с условным включением Telegram уведомлений.
        """
        config_instance = self.config()

        # Формируем список сервисов уведомлений
        notification_services = [self.email_sender()]

        # Добавляем Telegram только если он настроен и включен
        if (config_instance.notifications.telegram and
            config_instance.notifications.telegram.enabled and
            config_instance.notifications.telegram.bot_token and
            config_instance.notifications.telegram.chat_id):
            notification_services.append(self.telegram_sender())

        return MainHandler(
            email_service=self.email_service(),
            file_service=self.file_service(),
            sftp_service=self.sftp_service(),
            file_repo=self.processed_file_repo(),
            log_repo=self.operation_log_repo(),
            notification_service=notification_services,
        )

    # --- Health Check Service ---
    health_service: providers.Factory[HealthCheckService] = providers.Factory(
        HealthCheckService,
        db_engine=db_engine,
        sftp_config=config.provided.sftp,
    )
