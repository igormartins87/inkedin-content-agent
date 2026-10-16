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

# Importação dos Adaptadores de Infraestrutura
from src.infrastructure.collectors import ContextAggregatorCollector
from src.infrastructure.llm_provider import GroqLLMProvider
from src.infrastructure.notion_repo import NotionRepository
from src.infrastructure.gmail_notifier import GmailNotificationService

# Importação do Caso de Uso
from src.use_cases.generate_weekly_post import GenerateWeeklyPostUseCase

def main():
    # Instanciação dos adaptadores concretos (Dependency Injection Container)
    collector = ContextAggregatorCollector()
    llm_provider = GroqLLMProvider()
    repository = NotionRepository()
    notifier = GmailNotificationService()

    # Injeção de dependências no caso de uso
    use_case = GenerateWeeklyPostUseCase(
        collector=collector,
        llm_provider=llm_provider,
        repository=repository,
        notifier=notifier
    )

    # Execução
    use_case.execute()

if __name__ == "__main__":
    main()