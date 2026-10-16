import os
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from src.domain.interfaces import IVisualGenerator
from src.domain.models import PostDraft

class PillowVisualGeneratorAdapter(IVisualGenerator):
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_font(self, size: int):
        """Tenta carregar fonte do sistema de forma segura ou usa padrão."""
        font_names = ["arial.ttf", "calibri.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
        for fn in font_names:
            try:
                return ImageFont.truetype(fn, size)
            except Exception:
                continue
        return ImageFont.load_default()

    def generate_card(self, post: PostDraft) -> str:
        print("🎨 Gerando Card Visual para o LinkedIn (1080x1080)...", flush=True)

        # Dimensões padrão do LinkedIn (Quadrado HD)
        width, height = 1080, 1080
        
        # Paleta de Cores (Dark Tech Slate Theme)
        bg_color = (15, 23, 42)       # Slate 900
        card_bg = (30, 41, 59)        # Slate 800
        text_primary = (248, 250, 252)# White Slate
        text_secondary = (148, 163, 184) # Muted Slate
        accent_blue = (56, 189, 248)  # Sky Blue
        badge_bg = (14, 116, 144)     # Cyan Dark

        image = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(image)

        # 1. Desenha Moldura/Card Central com Cantos Suaves
        margin = 60
        card_bounds = [margin, margin, width - margin, height - margin]
        draw.rectangle(card_bounds, fill=card_bg, outline=badge_bg, width=3)

        # 2. Carrega Fontes
        font_title = self._get_font(42)
        font_body = self._get_font(30)
        font_meta = self._get_font(24)

        # 3. Badge do Pilar
        pillar_text = f"  {post.pillar.upper()}  "
        draw.rectangle([margin + 40, margin + 40, margin + 300, margin + 85], fill=badge_bg)
        draw.text((margin + 50, margin + 50), pillar_text, fill=(255, 255, 255), font=font_meta)

        # 4. Título do Post (Com quebra de linha inteligente)
        wrapped_title = textwrap.fill(post.title, width=28)
        draw.text((margin + 40, margin + 120), wrapped_title, fill=accent_blue, font=font_title)

        # 5. Destaque dos Ganchos / Conteúdo Principal (Primeiras linhas do post)
        lines = [line.strip() for line in post.content.splitlines() if line.strip()]
        snippet = "\n\n".join(lines[:4]) if lines else post.title
        wrapped_snippet = textwrap.fill(snippet, width=38)

        draw.text((margin + 40, margin + 320), wrapped_snippet, fill=text_primary, font=font_body)

        # 6. Rodapé de Marca Pessoal
        footer_y = height - margin - 80
        draw.line([(margin + 40, footer_y), (width - margin - 40, footer_y)], fill=text_secondary, width=1)
        
        footer_text = "🎯 Agente de Conteúdo | Dicas Diárias de Desenvolvimento & Carreira"
        draw.text((margin + 40, footer_y + 20), footer_text, fill=text_secondary, font=font_meta)

        # 7. Salva a imagem PNG
        output_path = self.output_dir / "linkedin_card.png"
        image.save(output_path, "PNG")
        print(f"  ✅ Card visual salvo em: {output_path.resolve()}", flush=True)

        return str(output_path.resolve())