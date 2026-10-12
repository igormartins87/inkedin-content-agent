import os
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

from fetch_context import load_clean_env
from generate_ideas import generate_ideas
from save_notion import save_ideas_to_notion
from send_email import send_notification_email

def run_agent():
    """Executa o fluxo completo do Agente de Conteúdo do LinkedIn."""
    print("="*60, flush=True)
    print("🚀 INICIANDO EXECUÇÃO DO LINKEDIN CONTENT AGENT", flush=True)
    print("="*60, flush=True)

    # 1. Carrega variáveis de ambiente
    load_clean_env()

    # 2. Gera os rascunhos de posts usando a IA + notícias + conhecimentos do Notion
    print("\n[Passo 1/3] 🤖 Gerando rascunhos de posts com a IA...", flush=True)
    ideas = generate_ideas()

    if not ideas:
        print("❌ Nenhuma ideia foi gerada. Interrompendo a execução.", flush=True)
        return

    print(f"✅ {len(ideas)} postagens geradas com sucesso!", flush=True)

    # 3. Salva os rascunhos no banco de dados do Notion
    print("\n[Passo 2/3] 📥 Salvando os rascunhos no Notion...", flush=True)
    saved_count = save_ideas_to_notion(ideas)

    if saved_count == 0:
        print("⚠️ Não foi possível salvar os posts no Notion. Verifique os logs acima.", flush=True)
        return

    print(f"✅ {saved_count} postagens salvas no banco 'Ideias de Post' do Notion!", flush=True)

    # 4. Envia a notificação por e-mail
    print("\n[Passo 3/3] 📧 Enviando notificação por e-mail...", flush=True)
    email_sent = send_notification_email(ideas)

    if email_sent:
        print("✅ E-mail de notificação enviado com sucesso!", flush=True)
    else:
        print("⚠️ Notificação por e-mail não enviada (verifique logs do SMTP).", flush=True)

    print("\n" + "="*60, flush=True)
    print("🎉 EXECUÇÃO CONCLUÍDA COM SUCESSO!", flush=True)
    print("="*60, flush=True)

if __name__ == "__main__":
    run_agent()