from abc import ABC, abstractmethod
from .models import PostDraft, WeeklyContext

class IContextCollector(ABC):
    @abstractmethod
    def fetch_context(self) -> WeeklyContext:
        pass

class ILLMProvider(ABC):
    @abstractmethod
    def generate_post(self, context: WeeklyContext) -> PostDraft:
        pass

class INotionRepository(ABC):
    @abstractmethod
    def save_post(self, post: PostDraft) -> bool:
        pass

    @abstractmethod
    def cleanup_old_posts(self, days: int = 30) -> int:
        pass

class IVisualGenerator(ABC):
    @abstractmethod
    def generate_card(self, post: PostDraft) -> str:
        """Gera o card visual do post e retorna o caminho do arquivo gerado."""
        pass

class INotificationService(ABC):
    @abstractmethod
    def send_notification(self, post: PostDraft) -> bool:
        pass