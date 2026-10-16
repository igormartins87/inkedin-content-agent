import os
from pathlib import Path
from dataclasses import dataclass

def load_clean_env():
    """Carrega o .env localizado na raiz tratando UTF-8 BOM e caminhos relativos."""
    project_root = Path(__file__).resolve().parent.parent.parent
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

def get_alias(*names) -> str:
    for n in names:
        v = os.getenv(n)
        if v and v.strip():
            return v.strip()
    return ""

@dataclass(frozen=True)
class Settings:
    NOTION_TOKEN: str = get_alias("NOTION_TOKEN", "NOTION_API_KEY", "NOTION_SECRET")
    NOTION_DATABASE_IDEAS_ID: str = get_alias("NOTION_DATABASE_IDEAS_ID", "NOTION_DATABASE_IDEIAS_ID") or "3de714ac-461f-80e5-af97-c64de001aede"
    NOTION_DATABASE_KNOWLEDGE_ID: str = get_alias("NOTION_DATABASE_KNOWLEDGE_ID", "NOTION_DATABASE_BASE_ID") or "3de714ac-461f-809c-be51-e509bf4336bc"
    GROQ_API_KEY: str = get_alias("GROQ_API_KEY")
    GMAIL_USER: str = get_alias("GMAIL_USER", "EMAIL_USER")
    GMAIL_APP_PASSWORD: str = get_alias("GMAIL_APP_PASSWORD", "EMAIL_PASS").replace(" ", "") if get_alias("GMAIL_APP_PASSWORD", "EMAIL_PASS") else ""

settings = Settings()