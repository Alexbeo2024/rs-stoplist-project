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

@pytest.mark.asyncio
class TestFileProcessingService:

    def test_initialization(self, tmp_path: Path):
        """Проверяет, что сервис корректно инициализируется."""
        service = FileProcessingService(base_storage_path=str(tmp_path))
        assert service.base_storage_path == str(tmp_path)

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
            sender="test@example.com",
            date=datetime(2024, 7, 30),
            attachments=[
                EmailAttachment(filename="report.xlsx", content=excel_bytes),
                EmailAttachment(filename="document.txt", content=b"some text"), # Другой тип файла для игнорирования
            ]
        )

        # --- Действие ---
        result_meta = await service.save_and_convert(fake_email)

        # --- Проверки ---
        assert len(result_meta) == 1 # Должен быть обработан только один файл
        meta = result_meta[0]

        # Проверка путей
        expected_base_dir = tmp_path / "ps" / "2024" / "07" / "30"
        expected_xlsx_path = expected_base_dir / "report.xlsx"
        expected_csv_path = expected_base_dir / "RS_stoplist_20240730.csv"

        assert Path(meta["file_path"]).resolve() == expected_xlsx_path.resolve()
        assert Path(meta["csv_path"]).resolve() == expected_csv_path.resolve()

        # Проверка, что файлы реально созданы
        assert expected_xlsx_path.exists()
        assert expected_csv_path.exists()

        # Проверка содержимого сохраненного xlsx
        with open(expected_xlsx_path, 'rb') as f:
            assert f.read() == excel_bytes

        # Проверка содержимого csv
        saved_csv_df = pd.read_csv(expected_csv_path)
        pd.testing.assert_frame_equal(saved_csv_df, fake_xlsx_content)

        # Проверка хеша
        assert "file_hash" in meta
        assert isinstance(meta["file_hash"], str)
        assert len(meta["file_hash"]) == 64 # SHA256
