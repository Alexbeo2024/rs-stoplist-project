# =====================================
# 1. Импорт библиотек
# =====================================
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

# =====================================
# 2. Базовые модели
# =====================================

class ProcessedFile(BaseModel):
    """
    Модель для представления информации об обработанном файле.
    Соответствует таблице processed_files в БД.
    """
    id: Optional[int] = Field(None, description="Уникальный идентификатор записи")
    message_id: str = Field(..., description="Уникальный идентификатор email-сообщения")
    sender_email: str = Field(..., description="Email отправителя")
    file_name: str = Field(..., description="Имя исходного файла")
    file_path: str = Field(..., description="Путь к сохраненному .xlsx файлу")
    csv_path: Optional[str] = Field(None, description="Путь к сконвертированному .csv файлу")
    sftp_uploaded: bool = Field(False, description="Статус загрузки на SFTP")
    file_hash: Optional[str] = Field(None, description="Хеш-сумма файла (SHA256)")
    processed_at: datetime = Field(default_factory=datetime.now, description="Время обработки")
    email_date: datetime = Field(..., description="Дата из заголовка письма")

    class Config:
        from_attributes = True

class OperationLog(BaseModel):
    """
    Модель для логов операций.
    Соответствует таблице operation_logs в БД.
    """
    id: Optional[int] = Field(None, description="Уникальный идентификатор записи")
    operation_type: str = Field(..., description="Тип операции (e.g., 'EMAIL_FETCH', 'FILE_CONVERT')")
    status: str = Field(..., description="Статус операции (SUCCESS, ERROR, WARNING)")
    message: Optional[str] = Field(None, description="Сообщение, связанное с операцией")
    context: Optional[Dict[str, Any]] = Field(None, description="Дополнительный контекст в формате JSON")
    created_at: datetime = Field(default_factory=datetime.now, description="Время создания лога")

    class Config:
        from_attributes = True
