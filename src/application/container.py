# =====================================
# 1. Импорт библиотек
# =====================================
from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import get_config # Импортируем функцию, а не объект
from src.domain.repositories import IProcessedFileRepository, IOperationLogRepository
from src.domain.services import IEmailReaderService, IFileProcessingService, ISftpUploadService
from src.domain.services.notifications import INotificationService
from src.infrastructure.email.email_reader import EmailReaderService
from src.infrastructure.notifications.email_sender import EmailSender
from src.infrastructure.notifications.telegram_sender import TelegramSender
from src.infrastructure.sftp.sftp_uploader import SftpUploadService
from src.infrastructure.storage.repositories import ProcessedFileRepository, OperationLogRepository
from src.infrastructure.storage.file_processor import FileProcessingService
from src.application.handlers.main_handler import MainHandler

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

    # --- Сервисы ---
    telegram_sender: providers.Factory[INotificationService] = providers.Factory(
        TelegramSender,
        config=config.provided.notifications.telegram,
    )

    email_sender: providers.Factory[INotificationService] = providers.Factory(
        EmailSender,
        config=config.provided.notifications.email,
    )

    # Композитный сервис, который отправляет по всем каналам
    notification_service: providers.List[INotificationService] = providers.List(
        telegram_sender,
        email_sender,
    )

    # --- Основные Сервисы ---
    email_reader_service: providers.Factory[IEmailReaderService] = providers.Factory(
        EmailReaderService,
        config=config.provided.email,
        processed_file_repo=processed_file_repo,
    )

    file_processing_service: providers.Factory[IFileProcessingService] = providers.Factory(
        FileProcessingService,
        base_storage_path="storage" # Можно вынести в конфиг позже
    )

    sftp_upload_service: providers.Factory[ISftpUploadService] = providers.Factory(
        SftpUploadService,
        config=config.provided.sftp,
    )

    # --- Обработчики ---
    main_handler: providers.Factory[MainHandler] = providers.Factory(
        MainHandler,
        email_service=email_reader_service,
        file_service=file_processing_service,
        sftp_service=sftp_upload_service,
        file_repo=processed_file_repo,
        log_repo=operation_log_repo,
        notification_service=notification_service,
    )
