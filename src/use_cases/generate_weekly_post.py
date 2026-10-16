from src.domain.interfaces import IContextCollector, ILLMProvider, INotionRepository, IVisualGenerator, INotificationService

class GenerateWeeklyPostUseCase:
    """Caso de uso principal: Coleta contexto -> Gera post -> Gera Card Visual -> Salva no Notion -> Notifica."""
    
    def __init__(
        self,
        collector: IContextCollector,
        llm_provider: ILLMProvider,
        repository: INotionRepository,
        visual_generator: IVisualGenerator,
        notifier: INotificationService
    ):
        self.collector = collector
        self.llm_provider = llm_provider
        self.repository = repository
        self.visual_generator = visual_generator
        self.notifier = notifier

    def execute(self) -> bool:
        print("="*60, flush=True)
        print("🚀 INICIANDO EXECUÇÃO (HEXAGONAL / SOLID + VISUAL CARD)", flush=True)
        print("="*60, flush=True)

        # 1. Coleta contexto
        context = self.collector.fetch_context()

        # 2. Gera o post via LLM
        post = self.llm_provider.generate_post(context)
        if not post or not post.content:
            print("❌ Falha na geração do post.", flush=True)
            return False

        # 3. Gera o Card Visual PNG
        card_path = self.visual_generator.generate_card(post)
        post.image_path = card_path

        # 4. Salva no Notion
        saved = self.repository.save_post(post)
        if not saved:
            print("❌ Falha ao salvar no Notion.", flush=True)
            return False

        # 5. Envia Notificação com a imagem anexada
        self.notifier.send_notification(post)

        print("\n" + "="*60, flush=True)
        print("🎉 EXECUÇÃO CONCLUÍDA COM SUCESSO!", flush=True)
        print("="*60, flush=True)
        return True