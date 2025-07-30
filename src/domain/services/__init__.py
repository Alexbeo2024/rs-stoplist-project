# =====================================
# 1. Импорт библиотек
# =====================================
from abc import ABC, abstractmethod
from typing import List, AsyncGenerator, NamedTuple, Optional
from datetime import datetime

# =====================================
# 2. Вспомогательные структуры данных
# =====================================

class EmailAttachment(NamedTuple):
    """Структура для хранения вложения из письма."""
    filename: str
    content: bytes

class RawEmail(NamedTuple):
    """Структура для хранения необработанного письма."""
    message_id: str
    sender: str
    date: datetime
    attachments: List[EmailAttachment]

# =====================================
# 3. Абстрактные интерфейсы сервисов
# =====================================

class IEmailReaderService(ABC):
    """
    Интерфейс для сервиса чтения писем.
    """
    @abstractmethod
    async def fetch_new_emails(self) -> AsyncGenerator[RawEmail, None]:
        """
        Асинхронный генератор для получения новых писем,
        которые соответствуют заданным критериям (отправитель, наличие вложений).
        """
        raise NotImplementedError
        yield

class IFileProcessingService(ABC):
    """
    Интерфейс для сервиса обработки файлов.
    """
    @abstractmethod
    async def save_and_convert(self, email: RawEmail) -> List[dict]:
        """
        Сохраняет вложения, конвертирует их в CSV и возвращает
        информацию о файлах для сохранения в БД.
        """
        raise NotImplementedError

class ISftpUploadService(ABC):
    """
    Интерфейс для сервиса загрузки файлов на SFTP.
    """
    @abstractmethod
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Загружает файл на SFTP-сервер.
        """
        raise NotImplementedError

    @abstractmethod
    async def upload_file_with_validation(self, local_path: str, remote_path: str, expected_hash: str) -> bool:
        """
        Загружает файл на SFTP-сервер с последующей проверкой целостности по хеш-сумме.

        Args:
            local_path: Путь к локальному файлу
            remote_path: Путь назначения на SFTP сервере
            expected_hash: Ожидаемая SHA256 хеш-сумма файла

        Returns:
            bool: True если загрузка и валидация успешны, False в противном случае
        """
        raise NotImplementedError
