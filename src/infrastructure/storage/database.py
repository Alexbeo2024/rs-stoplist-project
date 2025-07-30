# =====================================
# 1. Импорт библиотек
# =====================================
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# from src.config import config # Закомментировано до настройки .env

# =====================================
# 2. Настройка подключения к БД
# =====================================

# DATABASE_URL = (
#     f"postgresql+asyncpg://{config.db.user}:{config.db.password}"
#     f"@{config.db.host}:{config.db.port}/{config.db.name}"
# )

# ЗАГЛУШКА: Используем временный URL для in-memory SQLite для возможности запуска
# В реальной среде он будет заменен на DATABASE_URL.
DATABASE_URL = "sqlite+aiosqlite:///./test.db" # Временно

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

async_session_maker = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# =====================================
# 3. Функция для получения сессии
# =====================================

async def get_async_session() -> AsyncSession:
    """
    Зависимость для получения асинхронной сессии SQLAlchemy.
    """
    async with async_session_maker() as session:
        yield session
