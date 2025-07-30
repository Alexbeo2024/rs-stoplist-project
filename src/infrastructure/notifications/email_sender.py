# =====================================
# 1. Импорт библиотек
# =====================================
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.config import NotificationsConfig
from src.domain.services.notifications import INotificationService, AlertMessage

# =====================================
# 2. Реализация сервиса
# =====================================

class EmailSender(INotificationService):
    """
    Отправляет уведомления по Email.
    """
    def __init__(self, config: NotificationsConfig.Email):
        self.config = config
        print("EmailSender initialized")

    async def send(self, alert: AlertMessage) -> bool:
        """
        Отправляет форматированное сообщение по SMTP.
        """
        message = MIMEMultipart()
        message["From"] = self.config.smtp_user
        message["To"] = ", ".join(self.config.recipients)
        message["Subject"] = f"[{alert.level}] {alert.error_type} in {alert.service_name}"

        body = alert.to_formatted_string()
        message.attach(MIMEText(body, "plain"))

        try:
            await aiosmtplib.send(
                message,
                hostname=self.config.smtp_server,
                port=self.config.smtp_port,
                username=self.config.smtp_user,
                password=self.config.smtp_password,
                use_tls=True,
            )
            print(f"Email alert sent successfully to {self.config.recipients}")
            return True
        except Exception as e:
            print(f"Failed to send email alert: {e}")
            return False
