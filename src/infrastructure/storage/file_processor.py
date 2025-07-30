# =====================================
# 1. Импорт библиотек
# =====================================
import os
import hashlib
from typing import List

import pandas as pd

from src.domain.services import IFileProcessingService, RawEmail, EmailAttachment

# =====================================
# 2. Реализация сервиса
# =====================================

class FileProcessingService(IFileProcessingService):
    """
    Сервис для обработки файлов: сохранение, вычисление хеша, конвертация.
    """
    def __init__(self, base_storage_path: str = "storage"):
        """
        Инициализирует сервис.

        Args:
            base_storage_path: Корневая папка для сохранения файлов.
                               По умолчанию 'storage'.
        """
        self.base_storage_path = base_storage_path
        print("FileProcessingService initialized")

    async def save_and_convert(self, email: RawEmail) -> List[dict]:
        """
        Сохраняет, хеширует и конвертирует вложения.

        Создает структуру директорий, сохраняет оригинальный файл,
        конвертирует его в CSV с кодировкой UTF-8 with BOM.
        """
        print(f"Processing files for message {email.message_id}...")

        processed_files_metadata = []

        for attachment in email.attachments:
            if not attachment.filename.endswith('.xlsx'):
                print(f"Skipping non-xlsx file: {attachment.filename}")
                continue

            # 1. Создать путь storage/ps/{YYYY}/{MM}/{DD}/
            date_path = f"{email.date.year}/{email.date.month:02d}/{email.date.day:02d}"
            full_path = os.path.join(self.base_storage_path, "ps", date_path)
            os.makedirs(full_path, exist_ok=True)

            # 2. Сохранить .xlsx
            xlsx_path = os.path.join(full_path, attachment.filename)
            with open(xlsx_path, "wb") as f:
                f.write(attachment.content)

            # 3. Вычислить хеш
            file_hash = hashlib.sha256(attachment.content).hexdigest()

            # 4. Конвертировать в .csv
            csv_filename = f"RS_stoplist_{email.date.strftime('%Y%m%d')}.csv"
            csv_path = os.path.join(full_path, csv_filename)

            try:
                df = pd.read_excel(xlsx_path, engine='openpyxl')
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            except Exception as e:
                print(f"Error converting file {attachment.filename} to CSV: {e}")
                # В реальном приложении здесь будет логирование и, возможно,
                # отправка уведомления об ошибке.
                continue

            processed_files_metadata.append({
                "message_id": email.message_id,
                "sender_email": email.sender,
                "file_name": attachment.filename,
                "file_path": xlsx_path,
                "csv_path": csv_path,
                "file_hash": file_hash,
                "email_date": email.date,
            })

        return processed_files_metadata
