# =====================================
# 1. Импорт библиотек
# =====================================
from typing import Optional, List, Type, Dict

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import sessionmaker

from src.domain.models import ProcessedFile as ProcessedFileModel, OperationLog as OperationLogModel
from src.domain.repositories import IProcessedFileRepository, IOperationLogRepository
from src.infrastructure.storage.database import Base

# =====================================
# 2. Определение ORM моделей
# =====================================

class ProcessedFile(Base):
    __tablename__ = "processed_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[str] = mapped_column(unique=True, index=True)
    sender_email: Mapped[str]
    file_name: Mapped[str]
    file_path: Mapped[str]
    csv_path: Mapped[Optional[str]]
    sftp_uploaded: Mapped[bool] = mapped_column(default=False)
    file_hash: Mapped[Optional[str]]
    processed_at: Mapped[Optional[str]]
    email_date: Mapped[str]

class OperationLog(Base):
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    operation_type: Mapped[str]
    status: Mapped[str]
    message: Mapped[Optional[str]]
    context: Mapped[Optional[Dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[Optional[str]]


# =====================================
# 3. Базовая реализация репозитория
# =====================================

class SQLAlchemyRepository:
    model: Type[Base] = None

    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    async def add(self, data: dict) -> Base:
        async with self.session_factory() as session:
            instance = self.model(**data)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance

    async def get(self, id: int) -> Optional[Base]:
        async with self.session_factory() as session:
            return await session.get(self.model, id)

    async def list(self) -> List[Base]:
        async with self.session_factory() as session:
            stmt = select(self.model)
            result = await session.execute(stmt)
            return result.scalars().all()

# =====================================
# 4. Конкретные реализации репозиториев
# =====================================

class ProcessedFileRepository(SQLAlchemyRepository, IProcessedFileRepository):
    model = ProcessedFile

    async def add(self, file_data: ProcessedFileModel) -> ProcessedFileModel:
        async with self.session_factory() as session:
            db_file = self.model(**file_data.dict(exclude_unset=True))
            session.add(db_file)
            await session.commit()
            await session.refresh(db_file)
            return ProcessedFileModel.from_orm(db_file)

    async def find_by_message_id(self, message_id: str) -> Optional[ProcessedFileModel]:
        async with self.session_factory() as session:
            stmt = select(self.model).where(self.model.message_id == message_id)
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()
            return ProcessedFileModel.from_orm(instance) if instance else None

class OperationLogRepository(SQLAlchemyRepository, IOperationLogRepository):
    model = OperationLog

    async def add(self, log_data: OperationLogModel) -> OperationLogModel:
        async with self.session_factory() as session:
            db_log = self.model(**log_data.dict(exclude_unset=True))
            session.add(db_log)
            await session.commit()
            await session.refresh(db_log)
            return OperationLogModel.from_orm(db_log)
