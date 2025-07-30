# =====================================
# 1. Импорт библиотек
# =====================================
from src.domain.repositories import IProcessedFileRepository, IOperationLogRepository
from src.domain.services import IEmailReaderService, IFileProcessingService, ISftpUploadService
from src.domain.models import ProcessedFile, OperationLog

# =====================================
# 2. Реализация главного обработчика
# =====================================

class MainHandler:
    """
    Оркестратор, который управляет всем процессом обработки.
    """
    def __init__(
        self,
        email_service: IEmailReaderService,
        file_service: IFileProcessingService,
        sftp_service: ISftpUploadService,
        file_repo: IProcessedFileRepository,
        log_repo: IOperationLogRepository,
    ):
        self.email_service = email_service
        self.file_service = file_service
        self.sftp_service = sftp_service
        self.file_repo = file_repo
        self.log_repo = log_repo

    async def process_emails(self):
        """
        Основной метод, запускающий полный цикл обработки:
        1. Чтение новых писем.
        2. Обработка и конвертация вложений.
        3. Сохранение информации в БД.
        4. Загрузка на SFTP.
        5. Обновление статуса в БД.
        """
        async for email in self.email_service.fetch_new_emails():
            try:
                # Обработка файлов
                processed_files = await self.file_service.save_and_convert(email)

                for file_meta in processed_files:
                    # Сохранение в БД
                    db_entry = ProcessedFile(**file_meta)
                    created_file = await self.file_repo.add(db_entry)

                    # Загрузка на SFTP
                    upload_success = await self.sftp_service.upload_file(
                        local_path=created_file.csv_path,
                        remote_path=f"/upload/{created_file.file_name.replace('.xlsx', '.csv')}"
                    )

                    # Обновление статуса
                    if upload_success:
                        created_file.sftp_uploaded = True
                        # await self.file_repo.update(created_file) # <-- нужен метод update
                        print(f"File {created_file.csv_path} uploaded successfully.")

            except Exception as e:
                # Логирование ошибок
                await self.log_repo.add(OperationLog(
                    operation_type="EMAIL_PROCESSING",
                    status="ERROR",
                    message=f"Failed to process email {email.message_id}: {e}",
                    context={"message_id": email.message_id}
                ))
