# =====================================
# 1. Импорт библиотек
# =====================================
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.config import EmailConfig # Импортируем только модель
from src.domain.services import RawEmail, EmailAttachment
from src.infrastructure.email.email_reader import EmailReaderService
from src.domain.repositories import IProcessedFileRepository

# =====================================
# 3. Фейковые классы для имитации
# =====================================

class FakeMailMessage:
    def __init__(self, uid, from_, subject, date, attachments_data):
        self.uid = uid
        self.from_ = from_
        self.subject = subject
        self.date = date
        self.attachments = []
        for filename, payload in attachments_data:
            att = MagicMock()
            att.filename = filename
            att.payload = payload
            self.attachments.append(att)

class FakeMailBox:
    def __init__(self, server):
        self._server = server
        self.messages = []

    def login(self, username, password, initial_folder='INBOX'):
        # Имитируем успешный вход
        return self

    def fetch(self, criteria, seen, from_, mark_seen):
        # В нашем фейковом классе мы просто возвращаем все сообщения
        return self.messages

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

# =====================================
# 2. Тестовый класс (пересмотренный)
# =====================================

@pytest.mark.asyncio
class TestEmailReaderService:

    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        """Фикстура для имитации репозитория ProcessedFileRepository."""
        repo = MagicMock(spec=IProcessedFileRepository)
        repo.find_by_message_id = AsyncMock()
        return repo

    @pytest.fixture
    def email_config(self) -> EmailConfig:
        """Фикстура для конфигурации email. Теперь создается локально."""
        return EmailConfig(
            server="imap.test.com",
            port=993,
            username="test@user.com",
            password="password",
            allowed_senders=["sender@domain.com"]
        )

    def _create_fake_mail_message(self, uid, from_, subject, attachments_data=None):
        """Вспомогательная функция для создания фейкового email сообщения."""
        if attachments_data is None:
            attachments_data = []

        msg = MagicMock()
        msg.uid = uid
        msg.from_ = from_
        msg.subject = subject
        msg.date = datetime.now()

        attachments = []
        for filename, payload in attachments_data:
            att = MagicMock()
            att.filename = filename
            att.payload = payload
            attachments.append(att)

        msg.attachments = attachments
        return msg

    async def test_fetch_new_emails_success(self, mock_repo, email_config):
        """
        Проверяет успешное получение нового письма с .xlsx вложением.
        """
        # --- Подготовка ---
        service = EmailReaderService(config=email_config, processed_file_repo=mock_repo)
        mock_repo.find_by_message_id.return_value = None

        fake_message_data = {
            "uid": "test-uid-1",
            "from_": "sender@domain.com",
            "subject": "Test Email",
            "date": datetime.now(),
            "attachments_data": [("report.xlsx", b"xlsx_content")]
        }

        # --- Имитация ---
        fake_mailbox_instance = FakeMailBox(server=email_config.server)
        fake_mailbox_instance.messages = [FakeMailMessage(**fake_message_data)]

        # Заменяем класс MailBox на наш готовый экземпляр
        with patch('src.infrastructure.email.email_reader.MailBox', return_value=fake_mailbox_instance) as MockedMailBox:
            # --- Действие ---
            results = [email async for email in service.fetch_new_emails()]

            # --- Проверка ---
            assert len(results) == 1
            assert results[0].message_id == "test-uid-1"
            assert len(results[0].attachments) == 1
            assert results[0].attachments[0].filename == "report.xlsx"

    async def test_fetch_skips_already_processed_email(self, mock_repo, email_config):
        """Проверяет, что сервис пропускает уже обработанное письмо."""
        service = EmailReaderService(config=email_config, processed_file_repo=mock_repo)
        mock_repo.find_by_message_id.return_value = "some_processed_file" # Имитируем, что письмо есть в БД

        fake_mailbox_instance = FakeMailBox(server=email_config.server)
        fake_mailbox_instance.messages = [FakeMailMessage(
            uid="processed-uid-1", from_="sender@domain.com", subject="S", date=datetime.now(), attachments_data=[]
        )]

        with patch('src.infrastructure.email.email_reader.MailBox', return_value=fake_mailbox_instance):
            results = [email async for email in service.fetch_new_emails()]
            assert len(results) == 0
            mock_repo.find_by_message_id.assert_called_once_with("processed-uid-1")

    async def test_fetch_skips_email_without_xlsx_attachment(self, mock_repo, email_config):
        """Проверяет, что сервис пропускает письма без .xlsx вложений."""
        service = EmailReaderService(config=email_config, processed_file_repo=mock_repo)
        mock_repo.find_by_message_id.return_value = None

        fake_mailbox_instance = FakeMailBox(server=email_config.server)
        fake_mailbox_instance.messages = [FakeMailMessage(
            uid="no-xlsx-uid-1", from_="sender@domain.com", subject="S", date=datetime.now(),
            attachments_data=[("report.txt", b"text_content")]
        )]

        with patch('src.infrastructure.email.email_reader.MailBox', return_value=fake_mailbox_instance):
            results = [email async for email in service.fetch_new_emails()]
            assert len(results) == 0
