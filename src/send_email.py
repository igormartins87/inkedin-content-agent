import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

def load_clean_env():
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"
    if not env_path.exists():
        env_path = Path(".env")
    if env_path.exists():
        raw_bytes = env_path.read_bytes()
        clean_text = raw_bytes.decode("utf-8-sig")
        for line in clean_text.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip("'\"")

load_clean_env()

def get_alias(*names):
    for n in names:
        v = os.getenv(n)
        if v and v.strip():
            return v.strip()
    return None

GMAIL_USER = get_alias("GMAIL_USER", "EMAIL_USER", "SMTP_USER")
GMAIL_APP_PASSWORD = get_alias("GMAIL_APP_PASSWORD", "EMAIL_PASS", "SMTP_PASSWORD")

def send_notification_email(posts_summary):
    """Envia um e-mail formatado via Gmail SMTP notificando sobre novos rascunhos no Notion."""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("⚠️ Configurações de e-mail (GMAIL_USER ou GMAIL_APP_PASSWORD) ausentes no .env. Pulo envio de e-mail.", flush=True)
        return False

    recipient_email = GMAIL_USER  # Envia para você mesmo

    subject = "🚀 Novos Rascunhos para LinkedIn Prontos no Notion!"

    # Monta o resumo dos posts para o corpo do e-mail
    posts_html = ""
    for idx, post in enumerate(posts_summary, 1):
        titulo = post.get("titulo_ideia", f"Ideia {idx}")
        pilar = post.get("pilar", "Dev & Código")
        formato = post.get("formato", "Tutorial")
        conteudo = post.get("conteudo_post", "")[:180] + "..."

        posts_html += f"""
        <div style="background-color: #f4f6f8; border-left: 4px solid #0077b5; padding: 12px 16px; margin-bottom: 16px; border-radius: 4px;">
            <h3 style="margin: 0 0 6px 0; color: #333333;">{idx}. {titulo}</h3>
            <p style="margin: 0 0 8px 0; font-size: 13px; color: #666666;">
                <strong>Pilar:</strong> {pilar} | <strong>Formato:</strong> {formato}
            </p>
            <p style="margin: 0; font-size: 14px; color: #444444; white-space: pre-line;"><em>"{conteudo}"</em></p>
        </div>
        """

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #0077b5; margin-bottom: 10px;">🎯 Agente de Conteúdo LinkedIn</h2>
        <p>Olá! Seu agente semanal acabou de gerar e salvar <strong>{len(posts_summary)} novos rascunhos de posts</strong> no seu Notion.</p>
        
        <hr style="border: none; border-top: 1px solid #eeeeee; margin: 20px 0;">

        {posts_html}

        <p style="text-align: center; margin-top: 30px;">
            <a href="https://notion.so" style="background-color: #0077b5; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                Acessar Painel no Notion
            </a>
        </p>

        <p style="font-size: 12px; color: #888888; text-align: center; margin-top: 30px;">
            Este é um e-mail automático gerado pelo seu LinkedIn Content Agent.
        </p>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"LinkedIn Agent <{GMAIL_USER}>"
    msg["To"] = recipient_email

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        print(f"📧 Enviando e-mail de notificação para {recipient_email}...", flush=True)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, recipient_email, msg.as_string())
        print("✅ E-mail enviado com sucesso!", flush=True)
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail via Gmail SMTP: {e}", flush=True)
        return False

if __name__ == "__main__":
    # Teste isolado do e-mail
    test_posts = [
        {
            "titulo_ideia": "Post Teste de Notificação",
            "pilar": "Dev & Código",
            "formato": "Tutorial / Dica Prática",
            "conteudo_post": "Este é um post de teste para validar a notificação do agente."
        }
    ]
    send_notification_email(test_posts)