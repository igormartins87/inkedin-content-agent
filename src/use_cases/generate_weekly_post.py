from src.domain.interfaces import IContextCollector, ILLMProvider, INotionRepository, INotificationService

class GenerateWeeklyPostUseCase:
    """Caso de uso principal: Coleta contexto -> Gera post -> Salva no Notion -> Notifica."""
    
    def __init__(
        self,
        collector: IContextCollector,
        llm_provider: ILLMProvider,
        repository: INotionRepository,
        notifier: INotificationService
    ):
        self.collector = collector
        self.llm_provider = llm_provider
        self.repository = repository
        self.notifier = notifier

    def execute(self) -> bool:
        print("="*60, flush=True)
        print("🚀 INICIANDO EXECUÇÃO (CLEAN ARCHITECTURE / SOLID)", flush=True)
        print("="*60, flush=True)

        # 1. Coleta contexto
        context = self.collector.fetch_context()

        # 2. Gera o post via LLM
        post = self.llm_provider.generate_post(context)
        if not post or not post.content:
            print("❌ Falha na geração do post.", flush=True)
            return False

        # 3. Salva no Notion
        saved = self.repository.save_post(post)
        if not saved:
            print("❌ Falha ao salvar no Notion.", flush=True)
            return False

        # 4. Envia Notificação
        self.notifier.send_notification(post)

        print("\n" + "="*60, flush=True)
        print("🎉 EXECUÇÃO CONCLUÍDA COM SUCESSO!", flush=True)
        print("="*60, flush=True)
        return True