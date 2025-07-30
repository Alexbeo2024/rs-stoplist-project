# =====================================
# 1. Импорт библиотек
# =====================================
from typing import AsyncGenerator
from imap_tools import MailBox, AND

from src.config import EmailConfig
from src.domain.repositories import IProcessedFileRepository
from src.domain.services import IEmailReaderService, RawEmail, EmailAttachment

# =====================================
# 2. Реализация сервиса
# =====================================

class EmailReaderService(IEmailReaderService):
    """
    Сервис для чтения писем с использованием imap-tools.
    """
    def __init__(
        self,
        config: EmailConfig,
        processed_file_repo: IProcessedFileRepository,
    ):
        self.config = config
        self.repo = processed_file_repo
        print("EmailReaderService initialized")

    async def fetch_new_emails(self) -> AsyncGenerator[RawEmail, None]:
        """
        Получает новые письма от разрешенных отправителей,
        проверяет их на уникальность и извлекает вложения.
        """
        print("Fetching new emails...")
        try:
            with MailBox(self.config.server).login(
                self.config.username, self.config.password, initial_folder='INBOX'
            ) as mailbox:
                # Критерии поиска: непрочитанные письма от разрешенных отправителей
                criteria = AND(seen=False, from_=self.config.allowed_senders)

                for msg in mailbox.fetch(criteria, mark_seen=True):
                    print(f"Found new email: UID={msg.uid}, From={msg.from_}, Subject={msg.subject}")

                    message_id = msg.uid
                    if await self.repo.find_by_message_id(message_id):
                        print(f"Message {message_id} already processed. Skipping.")
                        continue

                    attachments = []
                    for att in msg.attachments:
                        if att.filename.endswith('.xlsx'):
                            attachments.append(EmailAttachment(
                                filename=att.filename,
                                content=att.payload
                            ))

                    if attachments:
                        yield RawEmail(
                            message_id=message_id,
                            sender=msg.from_,
                            date=msg.date,
                            attachments=attachments
                        )
                    else:
                        print(f"No .xlsx attachments found in message {message_id}. Skipping.")

        except Exception as e:
            print(f"Failed to fetch emails: {e}")
            # Здесь должно быть логирование и уведомление
            # await self.log_repo.add(...)
