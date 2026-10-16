import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

from src.infrastructure.collectors import ContextAggregatorCollector
from src.infrastructure.llm_provider import GroqLLMProvider
from src.infrastructure.notion_repo import NotionRepository
from src.infrastructure.visual_generator import PillowVisualGeneratorAdapter
from src.infrastructure.gmail_notifier import GmailNotificationService

from src.use_cases.generate_weekly_post import GenerateWeeklyPostUseCase

def main():
    # Instanciação dos adaptadores concretos (Hexagonal Architecture)
    collector = ContextAggregatorCollector()
    llm_provider = GroqLLMProvider()
    repository = NotionRepository()
    visual_generator = PillowVisualGeneratorAdapter()
    notifier = GmailNotificationService()

    # Injeção de dependências
    use_case = GenerateWeeklyPostUseCase(
        collector=collector,
        llm_provider=llm_provider,
        repository=repository,
        visual_generator=visual_generator,
        notifier=notifier
    )

    use_case.execute()

if __name__ == "__main__":
    main()