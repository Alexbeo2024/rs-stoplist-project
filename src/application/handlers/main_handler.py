# =====================================
# 1. Импорт библиотек
# =====================================
from typing import List

from src.domain.repositories import IProcessedFileRepository, IOperationLogRepository
from src.domain.services import IEmailReaderService, IFileProcessingService, ISftpUploadService
from src.domain.models import ProcessedFile, OperationLog
from src.domain.services.notifications import INotificationService, AlertMessage
from src.infrastructure.logging.logger import get_logger
from src.infrastructure.monitoring.metrics import metrics

# =====================================
# 2. Главный обработчик
# =====================================

class MainHandler:
    """
    Основной обработчик, координирующий всю цепочку обработки email.

    Объединяет работу сервисов email, обработки файлов, SFTP и уведомлений
    для реализации полного бизнес-процесса.
    """

    def __init__(
        self,
        email_service: IEmailReaderService,
        file_service: IFileProcessingService,
        sftp_service: ISftpUploadService,
        file_repo: IProcessedFileRepository,
        log_repo: IOperationLogRepository,
        notification_service: List[INotificationService],
    ):
        self.email_service = email_service
        self.file_service = file_service
        self.sftp_service = sftp_service
        self.file_repo = file_repo
        self.log_repo = log_repo
        self.notification_service = notification_service
        self.logger = get_logger(__name__)
        self.logger.info("MainHandler initialized with all required services")

    async def _send_alert(self, alert: AlertMessage) -> None:
        """
        Отправляет уведомление через все настроенные каналы.

        Args:
            alert: Сообщение для отправки
        """
        self.logger.debug(f"Sending alert: {alert.error_type}")
        for service in self.notification_service:
            try:
                await service.send(alert)
            except Exception as e:
                self.logger.error(f"Failed to send alert via {service.__class__.__name__}: {e}")

    async def process_emails(self) -> None:
        """
        Основной метод обработки: получает email, обрабатывает файлы, загружает на SFTP.
        """
        self.logger.info("Starting email processing cycle")

        processed_count = 0
        error_count = 0

        try:
            async for email in self.email_service.fetch_new_emails():
                try:
                    self.logger.info(f"Processing email from {email.sender} with {len(email.attachments)} attachments")

                    # Шаг 1: Обработка и сохранение файлов
                    processed_files = await self.file_service.save_and_convert(email)

                    if not processed_files:
                        self.logger.warning(f"No files were processed from email {email.message_id}")
                        continue

                    # Шаг 2: Сохранение метаданных в БД и загрузка на SFTP
                    for file_meta in processed_files:
                        self.logger.debug(f"Processing file metadata: {file_meta['file_name']}")

                        try:
                            # Сохранение в БД
                            db_entry = ProcessedFile(**file_meta)
                            created_file = await self.file_repo.add(db_entry)
                            self.logger.debug(f"File metadata saved to database with ID: {created_file.id}")

                            # Загрузка на SFTP с валидацией хеш-суммы
                            remote_filename = created_file.file_name.replace('.xlsx', '.csv')
                            remote_path = f"/upload/{remote_filename}"

                            self.logger.debug(f"Uploading {created_file.csv_path} to SFTP with hash validation")
                            upload_success = await self.sftp_service.upload_file_with_validation(
                                local_path=created_file.csv_path,
                                remote_path=remote_path,
                                expected_hash=created_file.file_hash
                            )

                            if upload_success:
                                # Обновляем статус загрузки в БД
                                created_file.sftp_uploaded = True
                                self.logger.info(f"File {created_file.file_name} successfully processed, uploaded and validated")

                                # Логгируем успешную операцию с валидацией
                                await self.log_repo.add(OperationLog(
                                    operation_type="FILE_UPLOAD_VALIDATED",
                                    status="SUCCESS",
                                    message=f"File {created_file.file_name} uploaded to SFTP and hash validated",
                                    context={
                                        "file_id": created_file.id,
                                        "remote_path": remote_path,
                                        "file_hash": created_file.file_hash
                                    }
                                ))
                            else:
                                self.logger.error(f"Failed to upload or validate {created_file.file_name} on SFTP")

                                # Отправляем уведомление о проблеме с SFTP/валидацией
                                alert = AlertMessage(
                                    level="ERROR",
                                    error_type="SftpUploadValidationError",
                                    service_name="MainHandler",
                                    message=f"Failed to upload or validate file {created_file.file_name} on SFTP after all retries",
                                    context={
                                        "file_name": created_file.file_name,
                                        "email_id": email.message_id,
                                        "expected_hash": created_file.file_hash
                                    }
                                )
                                await self._send_alert(alert)

                        except Exception as file_error:
                            self.logger.error(f"Error processing file {file_meta['file_name']}: {file_error}", exc_info=True)
                            error_count += 1

                            # Логгируем ошибку обработки файла
                            await self.log_repo.add(OperationLog(
                                operation_type="FILE_PROCESSING",
                                status="ERROR",
                                message=f"Error processing file {file_meta['file_name']}: {file_error}",
                                context={"file_name": file_meta['file_name'], "email_id": email.message_id}
                            ))

                    processed_count += 1
                    self.logger.info(f"Email {email.message_id} processing completed successfully")

                except Exception as email_error:
                    self.logger.error(f"Error processing email {email.message_id}: {email_error}", exc_info=True)
                    error_count += 1

                    # Отправляем критическое уведомление
                    alert = AlertMessage(
                        level="CRITICAL",
                        error_type=email_error.__class__.__name__,
                        service_name="MainHandler",
                        message=f"Failed to process email {email.message_id}: {email_error}",
                        context={"message_id": email.message_id, "sender": email.sender}
                    )
                    await self._send_alert(alert)

                    # Логгируем критическую ошибку
                    await self.log_repo.add(OperationLog(
                        operation_type="EMAIL_PROCESSING",
                        status="ERROR",
                        message=f"Failed to process email {email.message_id}: {email_error}",
                        context={"message_id": email.message_id, "sender": email.sender}
                    ))

        except Exception as general_error:
            self.logger.critical(f"Critical error in email processing cycle: {general_error}", exc_info=True)

            # Отправляем критическое системное уведомление
            alert = AlertMessage(
                level="CRITICAL",
                error_type=general_error.__class__.__name__,
                service_name="MainHandler",
                message=f"Email processing cycle failed: {general_error}",
                context={"processed_count": processed_count, "error_count": error_count}
            )
            await self._send_alert(alert)

        finally:
            # Обновляем метрики в конце цикла
            metrics.set_active_jobs(0)
            if processed_count > 0:
                metrics.update_last_successful_processing()

            self.logger.info(f"Email processing cycle completed. Processed: {processed_count}, Errors: {error_count}")
