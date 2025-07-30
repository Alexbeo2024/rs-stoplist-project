# =====================================
# 1. Импорт библиотек
# =====================================
from typing import Optional, List, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    context: Mapped[Optional[dict]]
    created_at: Mapped[Optional[str]]


# =====================================
# 3. Базовая реализация репозитория
# =====================================

class SQLAlchemyRepository:
    model: Type[Base] = None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, data: dict) -> Base:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def get(self, id: int) -> Optional[Base]:
        return await self.session.get(self.model, id)

    async def list(self) -> List[Base]:
        stmt = select(self.model)
        result = await self.session.execute(stmt)
        return result.scalars().all()

# =====================================
# 4. Конкретные реализации репозиториев
# =====================================

class ProcessedFileRepository(SQLAlchemyRepository, IProcessedFileRepository):
    model = ProcessedFile

    async def add(self, file_data: ProcessedFileModel) -> ProcessedFileModel:
        db_file = self.model(**file_data.dict())
        self.session.add(db_file)
        await self.session.commit()
        await self.session.refresh(db_file)
        return ProcessedFileModel.from_orm(db_file)

    async def find_by_message_id(self, message_id: str) -> Optional[ProcessedFileModel]:
        stmt = select(self.model).where(self.model.message_id == message_id)
        result = await self.session.execute(stmt)
        instance = result.scalar_one_or_none()
        return ProcessedFileModel.from_orm(instance) if instance else None

class OperationLogRepository(SQLAlchemyRepository, IOperationLogRepository):
    model = OperationLog

    async def add(self, log_data: OperationLogModel) -> OperationLogModel:
        db_log = self.model(**log_data.dict())
        self.session.add(db_log)
        await self.session.commit()
        await self.session.refresh(db_log)
        return OperationLogModel.from_orm(db_log)
