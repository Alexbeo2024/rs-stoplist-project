# =====================================
# 1. Импорт библиотек
# =====================================
from typing import AsyncGenerator
from imap_tools import MailBox

from src.config import EmailConfig
from src.domain.repositories import IProcessedFileRepository
from src.domain.services import IEmailReaderService, RawEmail, EmailAttachment
from src.infrastructure.logging.logger import get_logger

# =====================================
# 2. Сервис чтения Email
# =====================================

class EmailReaderService(IEmailReaderService):
    """
    Сервис для подключения к почтовому серверу и извлечения новых писем.

    Реализует проверку на дубликаты по message_id и фильтрацию
    по белому списку отправителей.
    """

    def __init__(
        self,
        config: EmailConfig,
        processed_file_repo: IProcessedFileRepository,
    ):
        self.config = config
        self.repo = processed_file_repo
        self.logger = get_logger(__name__)
        self.logger.info("EmailReaderService initialized")

    async def fetch_new_emails(self) -> AsyncGenerator[RawEmail, None]:
        """
        Асинхронно извлекает новые непрочитанные письма от разрешенных отправителей.

        Yields:
            RawEmail: Обработанное письмо с вложениями .xlsx
        """
        self.logger.info("Starting email fetch process")

        try:
            with MailBox(self.config.server).login(
                self.config.username, self.config.password, initial_folder='INBOX'
            ) as mailbox:
                self.logger.debug(f"Connected to mail server: {self.config.server}")

                # Передаем критерии напрямую в fetch
                messages_found = 0
                for msg in mailbox.fetch(criteria="ALL", seen=False, from_=self.config.allowed_senders, mark_seen=True):
                    messages_found += 1
                    self.logger.info(f"Processing email: UID={msg.uid}, From={msg.from_}, Subject={msg.subject}")

                    message_id = msg.uid # Используем UID, т.к. он стабилен в рамках сессии

                    # Проверка на дубликаты
                    if await self.repo.find_by_message_id(message_id):
                        self.logger.debug(f"Message {message_id} already processed, skipping")
                        continue

                    # Извлечение .xlsx вложений
                    xlsx_attachments = []
                    for att in msg.attachments:
                        if att.filename.endswith('.xlsx'):
                            xlsx_attachments.append(EmailAttachment(
                                filename=att.filename,
                                content=att.payload
                            ))
                            self.logger.debug(f"Found .xlsx attachment: {att.filename}")
                        else:
                            self.logger.debug(f"Skipping non-.xlsx attachment: {att.filename}")

                    if xlsx_attachments:
                        self.logger.info(f"Email {message_id} contains {len(xlsx_attachments)} .xlsx attachments")
                        yield RawEmail(
                            message_id=message_id,
                            sender=msg.from_,
                            date=msg.date,
                            attachments=xlsx_attachments
                        )
                    else:
                        self.logger.warning(f"No .xlsx attachments found in message {message_id}")

                self.logger.info(f"Email fetch completed. Processed {messages_found} messages")

        except Exception as e:
            self.logger.error(f"Failed to fetch emails: {e}", exc_info=True)
            raise
