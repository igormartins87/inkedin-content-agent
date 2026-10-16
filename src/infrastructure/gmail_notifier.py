import smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from src.domain.interfaces import INotificationService
from src.domain.models import PostDraft
from src.config.settings import settings

class GmailNotificationService(INotificationService):
    def send_notification(self, post: PostDraft) -> bool:
        if not settings.GMAIL_USER or not settings.GMAIL_APP_PASSWORD:
            print("⚠️ Configurações do Gmail ausentes no .env.", flush=True)
            return False

        recipient = settings.GMAIL_USER
        subject = "🚀 Novo Rascunho & Card Visual para LinkedIn Prontos no Notion!"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #0077b5;">🎯 Agente de Conteúdo LinkedIn</h2>
            <p>Seu agente semanal acabou de gerar e publicar <strong>1 novo post refinado com Card Visual</strong> no seu Notion.</p>
            
            <div style="background-color: #f4f6f8; border-left: 4px solid #0077b5; padding: 12px 16px; margin-bottom: 16px;">
                <h3 style="margin: 0 0 6px 0;">1. {post.title}</h3>
                <p style="margin: 0 0 8px 0; font-size: 13px; color: #666;">
                    <strong>Pilar:</strong> {post.pillar} | <strong>Formato:</strong> {post.suggested_format}
                </p>
                <p style="margin: 0; font-size: 14px; white-space: pre-line;"><em>"{post.content[:250]}..."</em></p>
            </div>

            <p><strong>🖼️ Card Visual Gerado para o Post:</strong></p>
            <p style="text-align: center;">
                <img src="cid:card_image" alt="Card Visual LinkedIn" style="max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #ddd;" />
            </p>

            <p style="text-align: center; margin-top: 30px;">
                <a href="https://notion.so" style="background-color: #0077b5; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                    Acessar Painel no Notion
                </a>
            </p>
        </body>
        </html>
        """

        msg = MIMEMultipart("related")
        msg["Subject"] = subject
        msg["From"] = f"LinkedIn Agent <{settings.GMAIL_USER}>"
        msg["To"] = recipient

        msg_alternative = MIMEMultipart("alternative")
        msg.attach(msg_alternative)
        msg_alternative.attach(MIMEText(html_body, "html", "utf-8"))

        # Anexa o Card PNG inline no corpo do e-mail
        if post.image_path and Path(post.image_path).exists():
            try:
                with open(post.image_path, "rb") as f:
                    img_data = f.read()
                    img = MIMEImage(img_data)
                    img.add_header("Content-ID", "<card_image>")
                    img.add_header("Content-Disposition", "inline", filename="linkedin_card.png")
                    msg.attach(img)
            except Exception as e:
                print(f"⚠️ Não foi possível anexar imagem no e-mail: {e}", flush=True)

        try:
            print(f"📧 Enviando e-mail de notificação com imagem para {recipient}...", flush=True)
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(settings.GMAIL_USER, settings.GMAIL_APP_PASSWORD)
                server.sendmail(settings.GMAIL_USER, recipient, msg.as_string())
            print("✅ E-mail com Card Visual enviado com sucesso!", flush=True)
            return True
        except Exception as e:
            print(f"❌ Erro ao enviar e-mail: {e}", flush=True)
            return False