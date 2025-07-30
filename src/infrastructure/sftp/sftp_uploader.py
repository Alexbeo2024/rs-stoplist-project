# =====================================
# 1. Импорт библиотек
# =====================================
import asyncio
import asyncssh

from src.config import SftpConfig
from src.domain.services import ISftpUploadService

# =====================================
# 2. Реализация сервиса
# =====================================

class SftpUploadService(ISftpUploadService):
    """
    Сервис для загрузки файлов на SFTP сервер с использованием asyncssh.
    """
    def __init__(self, config: SftpConfig):
        self.config = config
        self.connection_options = {
            "host": self.config.host,
            "username": self.config.username,
            "client_keys": [self.config.key_path]
        }
        print("SftpUploadService initialized")

    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Загружает файл на SFTP с 3 попытками и exponential backoff.
        """
        max_retries = 3
        delay = 1  # Начальная задержка в секундах

        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}/{max_retries}: Connecting to SFTP...")
                conn = await asyncssh.connect(**self.connection_options)
                try:
                    sftp = await conn.start_sftp_client()
                    try:
                        print(f"Uploading {local_path} to {remote_path}...")
                        await sftp.put(local_path, remote_path)
                        print("Upload successful.")
                        return True
                    finally:
                        sftp.exit()
                finally:
                    conn.close()
                    await conn.wait_closed()
            except (asyncssh.Error, OSError) as e:
                print(f"SFTP attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    print("All SFTP upload attempts failed.")
                    # Здесь будет логирование и отправка уведомления
                    return False
        return False
