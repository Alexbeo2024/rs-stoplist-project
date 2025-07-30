# =====================================
# 1. Импорт библиотек
# =====================================
import asyncio
import asyncssh  # type: ignore
import hashlib
import tempfile
import os

from src.config import SftpConfig
from src.domain.services import ISftpUploadService
from src.infrastructure.logging.logger import get_logger

# =====================================
# 2. Реализация сервиса SFTP
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

    async def upload_file_with_validation(self, local_path: str, remote_path: str, expected_hash: str) -> bool:
        """
        Загружает файл на SFTP с последующей проверкой целостности по хеш-сумме.

        Args:
            local_path: Путь к локальному файлу
            remote_path: Путь назначения на SFTP сервере
            expected_hash: Ожидаемая SHA256 хеш-сумма файла

        Returns:
            bool: True если загрузка и валидация успешны, False в противном случае
        """
        max_retries = 3
        delay = 1

        self.logger.info(f"Starting SFTP upload with validation: {local_path} -> {remote_path}")
        self.logger.debug(f"Expected SHA256 hash: {expected_hash[:16]}...")

        for attempt in range(max_retries):
            try:
                self.logger.debug(f"Attempt {attempt + 1}/{max_retries}: Connecting to SFTP server {self.config.host}")

                conn = await asyncssh.connect(**self.connection_options)
                try:
                    sftp = await conn.start_sftp_client()
                    try:
                        # 1. Загружаем файл на SFTP
                        self.logger.debug(f"SFTP client started, uploading file...")
                        await sftp.put(local_path, remote_path)
                        self.logger.debug(f"File uploaded to {remote_path}, starting validation...")

                        # 2. Проверяем целостность файла
                        is_valid = await self._validate_remote_file_hash(sftp, remote_path, expected_hash)

                        if is_valid:
                            self.logger.info(f"File {remote_path} successfully uploaded and validated")
                            return True
                        else:
                            self.logger.error(f"Hash validation failed for {remote_path}. File may be corrupted.")
                            # Удаляем поврежденный файл
                            try:
                                await sftp.remove(remote_path)
                                self.logger.debug(f"Removed corrupted file {remote_path}")
                            except Exception as remove_error:
                                self.logger.warning(f"Failed to remove corrupted file {remote_path}: {remove_error}")

                            # Продолжаем попытки
                            continue

                    finally:
                        sftp.exit()
                        self.logger.debug("SFTP client closed")
                finally:
                    conn.close()
                    await conn.wait_closed()
                    self.logger.debug("SSH connection closed")

            except (asyncssh.Error, OSError) as e:
                self.logger.warning(f"SFTP upload attempt {attempt + 1}/{max_retries} failed: {e}")

                if attempt < max_retries - 1:
                    self.logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    self.logger.error(f"All {max_retries} SFTP upload attempts failed for {local_path}")

        return False

    async def _validate_remote_file_hash(self, sftp, remote_path: str, expected_hash: str) -> bool:
        """
        Проверяет хеш-сумму файла на удаленном SFTP сервере.

        Args:
            sftp: Активный SFTP клиент
            remote_path: Путь к файлу на SFTP сервере
            expected_hash: Ожидаемая SHA256 хеш-сумма

        Returns:
            bool: True если хеши совпадают, False в противном случае
        """
        try:
            self.logger.debug(f"Validating hash for remote file: {remote_path}")

            # Создаем временный файл для скачивания
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name

            try:
                # Скачиваем файл с SFTP для проверки
                await sftp.get(remote_path, temp_path)
                self.logger.debug(f"Downloaded {remote_path} to {temp_path} for validation")

                # Вычисляем хеш скачанного файла
                actual_hash = await self._calculate_file_hash(temp_path)
                self.logger.debug(f"Actual SHA256 hash: {actual_hash[:16]}...")

                # Сравниваем хеши
                if actual_hash == expected_hash:
                    self.logger.debug(f"Hash validation successful for {remote_path}")
                    return True
                else:
                    self.logger.error(f"Hash mismatch for {remote_path}. Expected: {expected_hash[:16]}..., Got: {actual_hash[:16]}...")
                    return False

            finally:
                # Удаляем временный файл
                try:
                    os.unlink(temp_path)
                    self.logger.debug(f"Cleaned up temporary file: {temp_path}")
                except OSError as e:
                    self.logger.warning(f"Failed to clean up temporary file {temp_path}: {e}")

        except Exception as e:
            self.logger.error(f"Error during hash validation for {remote_path}: {e}", exc_info=True)
            return False

    async def _calculate_file_hash(self, file_path: str) -> str:
        """
        Асинхронно вычисляет SHA256 хеш файла.

        Args:
            file_path: Путь к файлу

        Returns:
            str: SHA256 хеш в hex формате
        """
        def _sync_hash_calculation():
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()

        # Выполняем вычисление хеша в executor для избежания блокировки event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_hash_calculation)
