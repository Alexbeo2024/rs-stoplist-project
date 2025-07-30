# =====================================
# 1. Импорт библиотек
# =====================================
import os
import hashlib
from typing import List
import pandas as pd

from src.domain.services import IFileProcessingService, RawEmail, EmailAttachment
from src.infrastructure.logging.logger import get_logger

# =====================================
# 2. Сервис обработки файлов
# =====================================

class FileProcessingService(IFileProcessingService):
    """
    Сервис для сохранения и конвертации Excel-файлов из email-вложений.

    Реализует сохранение в структурированную директорию по дате
    и конвертацию в CSV с UTF-8 BOM.
    """

    def __init__(self, base_storage_path: str = "storage"):
        self.base_storage_path = base_storage_path
        self.logger = get_logger(__name__)
        self.logger.info(f"FileProcessingService initialized with base path: {base_storage_path}")

    async def save_and_convert(self, email: RawEmail) -> List[dict]:
        """
        Сохраняет вложения email и конвертирует их в CSV.

        Args:
            email: Email с вложениями для обработки

        Returns:
            List[dict]: Метаданные обработанных файлов
        """
        self.logger.info(f"Processing files for message {email.message_id} from {email.sender}")
        processed_files_metadata = []

        for attachment in email.attachments:
            if not attachment.filename.endswith('.xlsx'):
                self.logger.debug(f"Skipping non-xlsx file: {attachment.filename}")
                continue

            self.logger.info(f"Processing .xlsx file: {attachment.filename}")

            # Создание структуры директорий по дате
            date_path = f"{email.date.year}/{email.date.month:02d}/{email.date.day:02d}"
            full_path = os.path.join(self.base_storage_path, "ps", date_path)
            os.makedirs(full_path, exist_ok=True)
            self.logger.debug(f"Created directory structure: {full_path}")

            # Сохранение исходного .xlsx файла
            xlsx_path = os.path.join(full_path, attachment.filename)
            with open(xlsx_path, "wb") as f:
                f.write(attachment.content)
            self.logger.debug(f"Saved .xlsx file to: {xlsx_path}")

            # Вычисление хеш-суммы
            file_hash = hashlib.sha256(attachment.content).hexdigest()
            self.logger.debug(f"Calculated SHA256 hash: {file_hash[:16]}...")

            # Конвертация в CSV
            csv_filename = f"RS_stoplist_{email.date.strftime('%Y%m%d')}.csv"
            csv_path = os.path.join(full_path, csv_filename)

            try:
                self.logger.debug(f"Converting {attachment.filename} to CSV format")
                df = pd.read_excel(xlsx_path, engine='openpyxl')
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                self.logger.info(f"Successfully converted to CSV: {csv_path}")

                # Логгирование статистики
                self.logger.debug(f"CSV contains {len(df)} rows and {len(df.columns)} columns")

            except Exception as e:
                self.logger.error(f"Error converting file {attachment.filename} to CSV: {e}", exc_info=True)
                continue

            # Сбор метаданных
            file_metadata = {
                "message_id": email.message_id,
                "sender_email": email.sender,
                "file_name": attachment.filename,
                "file_path": xlsx_path,
                "csv_path": csv_path,
                "file_hash": file_hash,
                "email_date": email.date,
            }
            processed_files_metadata.append(file_metadata)
            self.logger.info(f"File {attachment.filename} processed successfully")

        self.logger.info(f"Completed processing {len(processed_files_metadata)} files for message {email.message_id}")
        return processed_files_metadata
