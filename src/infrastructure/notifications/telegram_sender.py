# =====================================
# 1. Импорт библиотек
# =====================================
import httpx

from src.config import NotificationsConfig
from src.domain.services.notifications import INotificationService, AlertMessage

# =====================================
# 2. Реализация сервиса
# =====================================

class TelegramSender(INotificationService):
    """
    Отправляет уведомления в Telegram.
    """
    def __init__(self, config: NotificationsConfig.Telegram):
        self.config = config
        self.api_url = f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage"
        print("TelegramSender initialized")

    async def send(self, alert: AlertMessage) -> bool:
        """
        Отправляет сообщение в чат Telegram.
        """
        formatted_text = f"<pre>{alert.to_formatted_string()}</pre>"
        payload = {
            "chat_id": self.config.chat_id,
            "text": formatted_text,
            "parse_mode": "HTML"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_url, json=payload)
                response.raise_for_status()
                print(f"Telegram alert sent successfully to chat_id {self.config.chat_id}")
                return True
        except httpx.HTTPStatusError as e:
            print(f"Failed to send Telegram alert: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred while sending Telegram alert: {e}")
            return False
