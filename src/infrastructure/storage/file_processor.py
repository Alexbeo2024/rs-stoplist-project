# =====================================
# 1. Импорт библиотек
# =====================================
import os
import hashlib
from typing import List

# import pandas as pd # Будет использоваться для конвертации

from src.domain.services import IFileProcessingService, RawEmail

# =====================================
# 2. Реализация сервиса
# =====================================

class FileProcessingService(IFileProcessingService):
    """
    Сервис для обработки файлов: сохранение, вычисление хеша, конвертация.
    """
    def __init__(self):
        print("FileProcessingService initialized (placeholder)")

    async def save_and_convert(self, email: RawEmail) -> List[dict]:
        """
        Сохраняет, хеширует и конвертирует вложения.

        (ЗАГЛУШКА: в реальной реализации здесь будет логика
        создания директорий, сохранения файлов, вызова pandas для конвертации)
        """
        print(f"Processing files for message {email.message_id}... (placeholder)")

        processed_files_metadata = []

        for attachment in email.attachments:
            # 1. Создать путь ps/{YYYY}/{MM}/{DD}/
            base_path = f"ps/{email.date.year}/{email.date.month:02d}/{email.date.day:02d}"
            # os.makedirs(base_path, exist_ok=True) # <-- реальный код

            # 2. Сохранить .xlsx
            xlsx_path = os.path.join(base_path, attachment.filename)
            # with open(xlsx_path, "wb") as f:
            #     f.write(attachment.content)

            # 3. Вычислить хеш
            file_hash = hashlib.sha256(attachment.content).hexdigest()

            # 4. Конвертировать в .csv
            csv_filename = f"RS_stoplist_{email.date.strftime('%Y%m%d')}.csv"
            csv_path = os.path.join(base_path, csv_filename)
            # df = pd.read_excel(xlsx_path)
            # df.to_csv(csv_path, index=False, encoding='utf-8-sig')

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
