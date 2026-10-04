import os
import sys
import json
import requests
import unicodedata
import traceback
from datetime import datetime
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

print("🚀 Iniciando save_notion.py...", flush=True)

def load_clean_env():
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"
    if not env_path.exists():
        env_path = Path(".env")
    if env_path.exists():
        print(f"📄 Lendo .env de: {env_path}", flush=True)
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

NOTION_TOKEN = get_alias("NOTION_TOKEN", "NOTION_API_KEY", "NOTION_SECRET")
NOTION_DATABASE_IDEAS_ID = get_alias("NOTION_DATABASE_IDEAS_ID", "NOTION_DATABASE_IDEIAS_ID")

if not NOTION_DATABASE_IDEAS_ID:
    NOTION_DATABASE_IDEAS_ID = "3de714ac-461f-80e5-af97-c64de001aede"

if not NOTION_TOKEN:
    print("❌ Token do Notion não encontrado no .env!", flush=True)
    raise SystemExit(1)

from generate_ideas import generate_ideas

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def normalize(s):
    return unicodedata.normalize('NFKD', s).encode('ASCII','ignore').decode('ASCII').lower().strip()

def get_schema():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_IDEAS_ID}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code != 200:
        print(f"❌ Erro ao ler schema do Notion: {r.status_code} - {r.text}")
        return {}
    props = r.json().get("properties", {})
    print(f"📋 Colunas encontradas no Notion: {list(props.keys())}", flush=True)
    return props

def build_select_payload(prop_def, desired_name):
    ptype = prop_def.get("type")
    if ptype == "select":
        return {"select": {"name": desired_name}}
    if ptype == "multi_select":
        return {"multi_select": [{"name": desired_name}]}
    if ptype == "status":
        opts = prop_def.get("status", {}).get("options", [])
        names = [o["name"] for o in opts]
        if desired_name in names:
            return {"status": {"name": desired_name}}
        elif names:
            return {"status": {"name": names[0]}}
    return None

def save_ideas_to_notion(ideas):
    if not ideas:
        print("⚠️ Nenhuma ideia para salvar.", flush=True)
        return 0

    schema_props = get_schema()
    if not schema_props:
        return 0

    map_names = {}
    for real_name, prop in schema_props.items():
        norm = normalize(real_name)
        ptype = prop.get("type")
        if ptype == "title" or norm in ["titulo", "title"]:
            map_names["title"] = real_name
        if "pilar" in norm:
            map_names["pilar"] = real_name
        if "formato" in norm:
            map_names["formato"] = real_name
        if "rascunho" in norm:
            map_names["rascunho"] = real_name
        if "status" in norm:
            map_names["status"] = real_name
        if "data" in norm:
            map_names["data"] = real_name

    url = "https://api.notion.com/v1/pages"
    saved = 0
    today_str = datetime.now().strftime("%Y-%m-%d")

    for idx, item in enumerate(ideas, 1):
        if isinstance(item, str):
            item = {
                "titulo_ideia": f"Post Gerado {idx}",
                "pilar": "Dev & Código",
                "formato": "Tutorial / Dica Prática",
                "conteudo_post": item
            }

        titulo = item.get("titulo_ideia", f"Nova Ideia {idx}")[:100]
        pilar = item.get("pilar", "Dev & Código")
        formato = item.get("formato", "Tutorial / Dica Prática")
        conteudo = item.get("conteudo_post", "")

        print(f"\n📝 Salvando no Notion: '{titulo}'...", flush=True)
        properties = {}

        if "title" in map_names:
            properties[map_names["title"]] = {"title": [{"text": {"content": titulo}}]}
        if "pilar" in map_names:
            payload = build_select_payload(schema_props[map_names["pilar"]], pilar)
            if payload:
                properties[map_names["pilar"]] = payload
        if "formato" in map_names:
            payload = build_select_payload(schema_props[map_names["formato"]], formato)
            if payload:
                properties[map_names["formato"]] = payload
        if "status" in map_names:
            payload = build_select_payload(schema_props[map_names["status"]], "💡 Ideia / Rascunho")
            if payload:
                properties[map_names["status"]] = payload
        if "rascunho" in map_names:
            chunks = [conteudo[i:i+1900] for i in range(0, len(conteudo), 1900)] or [""]
            rich = [{"text": {"content": c}} for c in chunks]
            properties[map_names["rascunho"]] = {"rich_text": rich}
        if "data" in map_names:
            properties[map_names["data"]] = {"date": {"start": today_str}}

        try:
            resp = requests.post(url, headers=HEADERS, json={"parent": {"database_id": NOTION_DATABASE_IDEAS_ID}, "properties": properties}, timeout=30)
            if resp.status_code == 200:
                print(f"  ✅ Salvo com sucesso!", flush=True)
                saved += 1
            else:
                print(f"  ❌ Erro {resp.status_code}: {resp.text}", flush=True)
        except Exception as e:
            print(f"  ❌ Exceção: {e}", flush=True)

    return saved

if __name__ == "__main__":
    print("🔍 Gerando ideias...", flush=True)
    ideas = generate_ideas()
    print(f"\n📦 {len(ideas)} ideias geradas, enviando para Notion...", flush=True)
    saved = save_ideas_to_notion(ideas)
    print(f"\n🎉 FIM! {saved}/{len(ideas)} posts salvos no Notion! Dê F5 no Notion.", flush=True)