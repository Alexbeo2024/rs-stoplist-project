# =====================================
# 1. Импорт библиотек
# =====================================
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field

# =====================================
# 2. Модель для сообщения
# =====================================

class AlertMessage(BaseModel):
    """
    Структурированное сообщение для отправки уведомлений.
    """
    level: str = Field("ERROR", description="Уровень (ERROR, WARNING, INFO)")
    error_type: str = Field(..., description="Тип ошибки (e.g., DatabaseConnectionError)")
    service_name: str = Field(..., description="Имя сервиса, где произошла ошибка")
    timestamp: datetime = Field(default_factory=datetime.now, description="Время возникновения")
    message: str = Field(..., description="Основное сообщение об ошибке")
    context: Optional[Dict[str, Any]] = Field(None, description="Дополнительный контекст")

    def to_formatted_string(self) -> str:
        """Конвертирует сообщение в форматированную строку."""
        title = f"[{self.level}] {self.error_type} in {self.service_name}"

        context_lines = []
        if self.context:
            for key, value in self.context.items():
                context_lines.append(f"  - {key}: {value}")
        context_str = "\n".join(context_lines)

        return (
            f"{title}\n"
            f"Time: {self.timestamp.isoformat()}\n"
            f"Message: {self.message}\n"
            f"Context:\n{context_str}"
        )

# =====================================
# 3. Абстрактный интерфейс сервиса
# =====================================

class INotificationService(ABC):
    """
    Абстрактный интерфейс для сервиса отправки уведомлений.
    """
    @abstractmethod
    async def send(self, alert: AlertMessage) -> bool:
        """
        Отправляет форматированное уведомление.
        """
        raise NotImplementedError
