# =====================================
# 1. Импорт библиотек
# =====================================
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Any

from src.domain.models import ProcessedFile, OperationLog

# =====================================
# 2. Определение Generic-типов
# =====================================
T = TypeVar("T")

# =====================================
# 3. Абстрактный базовый репозиторий
# =====================================

class AbstractRepository(ABC, Generic[T]):
    """
    Абстрактный базовый класс для репозиториев.
    Определяет стандартный набор CRUD-операций.
    """

    @abstractmethod
    async def add(self, data: T) -> T:
        raise NotImplementedError

    @abstractmethod
    async def get(self, id: Any) -> Optional[T]:
        raise NotImplementedError

    @abstractmethod
    async def list(self) -> List[T]:
        raise NotImplementedError

# =====================================
# 4. Абстрактные репозитории для моделей
# =====================================

class IProcessedFileRepository(AbstractRepository[ProcessedFile], ABC):
    """
    Интерфейс для репозитория обработанных файлов.
    """
    @abstractmethod
    async def find_by_message_id(self, message_id: str) -> Optional[ProcessedFile]:
        """Ищет файл по уникальному ID сообщения."""
        raise NotImplementedError

class IOperationLogRepository(AbstractRepository[OperationLog], ABC):
    """
    Интерфейс для репозитория логов операций.
    """
    pass # На данный момент стандартных CRUD операций достаточно
