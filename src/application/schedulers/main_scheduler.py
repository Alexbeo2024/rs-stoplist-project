# =====================================
# 1. Импорт библиотек
# =====================================
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.application.container import Container
from src.application.handlers.main_handler import MainHandler

# =====================================
# 2. Глобальный экземпляр планировщика
# =====================================
scheduler = AsyncIOScheduler()

# =====================================
# 3. Функция для запуска обработки
# =====================================

async def trigger_email_processing():
    """
    Функция-обертка, которая получает MainHandler из контейнера
    и запускает процесс обработки писем.
    """
    container = Container()
    handler: MainHandler = await container.main_handler()
    print("Scheduler triggered: Starting email processing...")
    await handler.process_emails()
    print("Email processing finished.")

# =====================================
# 4. Настройка и запуск задачи
# =====================================

def setup_scheduler():
    """
    Настраивает и запускает задачу по обработке email.
    """
    container = Container()
    interval = container.config.scheduler.interval_hours()

    scheduler.add_job(
        trigger_email_processing,
        'interval',
        hours=interval,
        id='email_processing_job',
        replace_existing=True
    )

    if not scheduler.running:
        scheduler.start()
        print(f"Scheduler started. Job will run every {interval} hour(s).")

def shutdown_scheduler():
    """
    Останавливает планировщик.
    """
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler shut down.")
