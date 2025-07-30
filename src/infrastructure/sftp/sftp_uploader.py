# =====================================
# 1. Импорт библиотек
# =====================================
import asyncio
import asyncssh  # type: ignore

from src.config import SftpConfig
from src.domain.services import ISftpUploadService
from src.infrastructure.logging.logger import get_logger

# =====================================
# 2. Сервис загрузки файлов на SFTP
# =====================================

class SftpUploadService(ISftpUploadService):
    """
    Сервис для загрузки файлов на SFTP с повторными попытками.

    Реализует аутентификацию по ключу и механизм exponential backoff
    для обработки временных сбоев сети.
    """

    def __init__(self, config: SftpConfig):
        self.config = config
        self.connection_options = {
            "host": self.config.host,
            "username": self.config.username,
            "client_keys": [self.config.key_path]
        }
        self.logger = get_logger(__name__)
        self.logger.info(f"SftpUploadService initialized for host: {self.config.host}")

    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Загружает файл на SFTP с 3 попытками и exponential backoff.

        Args:
            local_path: Путь к локальному файлу
            remote_path: Путь назначения на SFTP сервере

        Returns:
            bool: True если загрузка успешна, False в противном случае
        """
        max_retries = 3
        delay = 1  # Начальная задержка в секундах

        self.logger.info(f"Starting SFTP upload: {local_path} -> {remote_path}")

        for attempt in range(max_retries):
            try:
                self.logger.debug(f"Attempt {attempt + 1}/{max_retries}: Connecting to SFTP server {self.config.host}")

                conn = await asyncssh.connect(**self.connection_options)
                try:
                    sftp = await conn.start_sftp_client()
                    try:
                        self.logger.debug(f"SFTP client started, uploading file...")
                        await sftp.put(local_path, remote_path)
                        self.logger.info(f"File successfully uploaded to {remote_path}")
                        return True
                    finally:
                        sftp.exit()
                        self.logger.debug("SFTP client closed")
                finally:
                    conn.close()
                    await conn.wait_closed()
                    self.logger.debug("SSH connection closed")

            except (asyncssh.Error, OSError) as e:
                self.logger.warning(f"SFTP attempt {attempt + 1}/{max_retries} failed: {e}")

                if attempt < max_retries - 1:
                    self.logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    self.logger.error(f"All {max_retries} SFTP upload attempts failed for {local_path}")

        return False
