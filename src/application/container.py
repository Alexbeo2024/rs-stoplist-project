# =====================================
# 1. Импорт библиотек
# =====================================
from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import config
from src.domain.repositories import IProcessedFileRepository, IOperationLogRepository
from src.domain.services import IEmailReaderService, IFileProcessingService, ISftpUploadService
from src.infrastructure.email.email_reader import EmailReaderService
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
    # -------------------
    # Конфигурация
    # -------------------
    config = providers.Configuration()
    config.from_dict(config.to_dict())

    # -------------------
    # Ядро: База данных
    # -------------------
    db_engine = providers.Singleton(
        create_async_engine,
        # url=config.db_url # Заменить, когда будет реальный URL
        url="sqlite+aiosqlite:///./test.db"
    )

    db_session_factory = providers.Singleton(
        sessionmaker,
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # -------------------
    # Репозитории
    # -------------------
    processed_file_repo: providers.Factory[IProcessedFileRepository] = providers.Factory(
        ProcessedFileRepository,
        session_factory=db_session_factory,
    )

    operation_log_repo: providers.Factory[IOperationLogRepository] = providers.Factory(
        OperationLogRepository,
        session_factory=db_session_factory,
    )

    # -------------------
    # Сервисы
    # -------------------
    email_reader_service: providers.Factory[IEmailReaderService] = providers.Factory(
        EmailReaderService,
        config=config.email,
        processed_file_repo=processed_file_repo,
    )

    file_processing_service: providers.Factory[IFileProcessingService] = providers.Factory(
        FileProcessingService,
    )

    sftp_upload_service: providers.Factory[ISftpUploadService] = providers.Factory(
        SftpUploadService,
        config=config.sftp,
    )

    # -------------------
    # Обработчики
    # -------------------
    main_handler: providers.Factory[MainHandler] = providers.Factory(
        MainHandler,
        email_service=email_reader_service,
        file_service=file_processing_service,
        sftp_service=sftp_upload_service,
        file_repo=processed_file_repo,
        log_repo=operation_log_repo,
    )
