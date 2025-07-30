# =====================================
# 1. Импорт библиотек
# =====================================
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.application.container import Container
from src.application.handlers.main_handler import MainHandler
from src.infrastructure.logging.logger import get_logger

# =====================================
# 2. Настройка планировщика
# =====================================

scheduler = AsyncIOScheduler()
logger = get_logger(__name__)

async def trigger_email_processing():
    """
    Задача планировщика для запуска обработки email.

    Создает новый экземпляр контейнера и обработчика для каждого запуска,
    обеспечивая изоляцию между выполнениями.
    """
    logger.info("Scheduler triggered: Starting email processing task")

    try:
        container = Container()
        handler: MainHandler = await container.main_handler()

        await handler.process_emails()
        logger.info("Email processing task completed successfully")

    except Exception as e:
        logger.error(f"Email processing task failed: {e}", exc_info=True)
        # В реальном приложении здесь может быть отправка критического уведомления

def setup_scheduler():
    """
    Настраивает и запускает планировщик задач.
    """
    try:
        container = Container()
        config = container.config()
        interval = config.scheduler.interval_hours

        logger.info(f"Setting up scheduler with {interval} hour(s) interval")

        scheduler.add_job(
            trigger_email_processing,
            'interval',
            hours=interval,
            id='email_processing_job',
            replace_existing=True,
            max_instances=1,  # Предотвращаем параллельное выполнение
            coalesce=True,    # Объединяем пропущенные запуски
        )

        if not scheduler.running:
            scheduler.start()
            logger.info(f"Scheduler started successfully. Job will run every {interval} hour(s)")
        else:
            logger.warning("Scheduler was already running")

    except Exception as e:
        logger.error(f"Failed to setup scheduler: {e}", exc_info=True)
        raise

def shutdown_scheduler():
    """
    Корректно останавливает планировщик.
    """
    try:
        if scheduler.running:
            scheduler.shutdown(wait=True)
            logger.info("Scheduler shut down successfully")
        else:
            logger.warning("Scheduler was not running")
    except Exception as e:
        logger.error(f"Error during scheduler shutdown: {e}", exc_info=True)
