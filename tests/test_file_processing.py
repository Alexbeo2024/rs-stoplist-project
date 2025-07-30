# =====================================
# 1. Импорт библиотек
# =====================================
import pytest
import pandas as pd
from datetime import datetime
from pathlib import Path

from src.domain.services import RawEmail, EmailAttachment
from src.infrastructure.storage.file_processor import FileProcessingService

# =====================================
# 2. Тестовый класс
# =====================================

class TestFileProcessingService:

    def test_initialization(self, tmp_path: Path):
        """Проверяет, что сервис корректно инициализируется."""
        service = FileProcessingService(base_storage_path=str(tmp_path))
        assert service.base_storage_path == str(tmp_path)

    @pytest.mark.asyncio
    async def test_save_and_convert_success(self, tmp_path: Path):
        """
        Проверяет успешное сохранение и конвертацию xlsx файла.
        """
        # --- Подготовка ---
        service = FileProcessingService(base_storage_path=str(tmp_path))

        # Создаем фейковый xlsx файл в памяти
        fake_xlsx_content = pd.DataFrame({'col1': [1, 2], 'col2': ['A', 'B']})
        excel_bytes_io = pd.io.common.BytesIO()
        with pd.ExcelWriter(excel_bytes_io, engine='openpyxl') as writer:
            fake_xlsx_content.to_excel(writer, index=False, sheet_name='Sheet1')
        excel_bytes = excel_bytes_io.getvalue()

        fake_email = RawEmail(
            message_id="test-msg-123",
            sender="test@sender.com",
            date=datetime(2023, 1, 15),
            attachments=[
                EmailAttachment(filename="report.xlsx", content=excel_bytes)
            ]
        )

        # --- Действие ---
        result_meta = await service.save_and_convert(fake_email)

        # --- Проверка ---
        # 1. Проверяем метаданные
        assert len(result_meta) == 1
        meta = result_meta[0]
        assert meta['file_name'] == "report.xlsx"
        assert meta['file_hash'] is not None

        # 2. Проверяем созданные файлы
        csv_path = Path(meta['csv_path'])
        assert csv_path.exists()
        assert csv_path.name == "RS_stoplist_20230115.csv"

        # 3. Проверяем содержимое CSV
        df = pd.read_csv(csv_path)
        pd.testing.assert_frame_equal(df, fake_xlsx_content)
