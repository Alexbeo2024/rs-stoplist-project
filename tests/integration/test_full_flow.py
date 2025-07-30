# =====================================
# 1. Импорт библиотек
# =====================================
import os
import pytest
import asyncssh
import pandas as pd
from datetime import datetime
from pathlib import Path
import asyncio

from src.application.container import Container
from src.domain.services import RawEmail, EmailAttachment

# =====================================
# 2. Настройка теста
# =====================================

# Пропускаем все тесты в этом файле, если не установлена переменная для интеграционных тестов
if os.getenv("APP_ENV") != "test":
    pytest.skip("Skipping integration tests", allow_module_level=True)

# =====================================
# 3. Тестовый класс
# =====================================

@pytest.mark.asyncio
class TestFullFlow:

    @pytest.fixture(scope="class")
    def event_loop(self):
        """Создает экземпляр event loop для всего тестового класса."""
        loop = asyncio.get_event_loop_policy().new_event_loop()
        yield loop
        loop.close()

    @pytest.fixture(scope="class")
    def container(self) -> Container:
        """Инициализирует DI контейнер."""
        container = Container()
        # Убедимся, что контейнер использует тестовую конфигурацию
        # Это должно быть установлено через .env файл перед запуском тестов
        return container

    async def test_file_processing_and_upload(self, container: Container, tmp_path: Path):
        """
        Проверяет полный цикл: создание файла -> конвертация -> загрузка на SFTP.
        """
        # --- 1. Подготовка ---
        file_processing_service = await container.file_processing_service()
        sftp_upload_service = await container.sftp_upload_service()
        sftp_config = container.config.sftp()

        # Создаем фейковый email и вложение
        fake_xlsx_content = pd.DataFrame({'col1': [10, 20], 'col2': ['C', 'D']})
        excel_bytes_io = pd.io.common.BytesIO()
        with pd.ExcelWriter(excel_bytes_io, engine='openpyxl') as writer:
            fake_xlsx_content.to_excel(writer, index=False, sheet_name='Sheet1')
        excel_bytes = excel_bytes_io.getvalue()

        fake_email = RawEmail(
            message_id="integration-test-123",
            sender="integration@test.com",
            date=datetime.now(),
            attachments=[EmailAttachment(filename="integration_report.xlsx", content=excel_bytes)]
        )

        # --- 2. Действие: Обработка и загрузка ---
        # Переопределяем базовый путь для хранения файлов на временную директорию
        file_processing_service.base_storage_path = str(tmp_path)

        processed_meta = await file_processing_service.save_and_convert(fake_email)
        assert len(processed_meta) == 1

        csv_local_path = processed_meta[0]['csv_path']
        csv_filename = Path(csv_local_path).name
        remote_path = f"{sftp_config['remote_path']}/{csv_filename}"

        upload_success = await sftp_upload_service.upload_file(csv_local_path, remote_path)
        assert upload_success is True

        # --- 3. Проверка: Файл на SFTP ---
        # Подключаемся к SFTP серверу из docker-compose и проверяем наличие файла
        async with asyncssh.connect(
            host=sftp_config['host'],
            port=2222, # Мы мапим порт 2222 на 22 в docker-compose
            username=sftp_config['username'],
            password="pass" # Пароль из docker-compose command
        ) as conn:
            async with conn.start_sftp_client() as sftp:
                assert await sftp.exists(remote_path) is True
                # (Опционально) Можно скачать файл и проверить его содержимое
                # local_download_path = tmp_path / "downloaded.csv"
                # await sftp.get(remote_path, str(local_download_path))
                # df = pd.read_csv(local_download_path)
                # assert df.shape == (2, 2)
