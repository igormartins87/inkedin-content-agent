import sys
import requests
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

def load_clean_env():
    """Carrega variaveis do .env limpas sem erros de encoding do Windows."""
    if not ENV_PATH.exists():
        return {}
    raw_bytes = ENV_PATH.read_bytes()
    if raw_bytes.startswith(b'\xef\xbb\xbf'):
        raw_bytes = raw_bytes[3:]
    env_vars = {}
    for line in raw_bytes.decode('utf-8', errors='ignore').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        env_vars[k.strip().replace('\ufeff', '')] = v.strip().strip('"').strip("'").replace('\ufeff', '')
    return env_vars

ENV = load_clean_env()
NOTION_KEY = ENV.get("NOTION_API_KEY", "")
BASE_DB_ID = ENV.get("NOTION_DATABASE_BASE_ID", "")


def fetch_external_news():
    """Busca as noticias e pensoes de tech em alta no TabNews (PT-BR) e Dev.to."""
    print("📡 Coletando tendencias e noticias tech externas...")
    items = []
    
    # 1. TabNews API (PT-BR)
    try:
        url = "https://www.tabnews.com.br/api/v1/contents?page=1&per_page=5&strategy=relevant"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            posts = res.json()
            for p in posts:
                items.append({
                    "fonte": "TabNews (BR)",
                    "titulo": p.get("title", ""),
                    "resumo": f"Discussão relevante na comunidade dev BR."
                })
    except Exception as e:
        print(f"  ⚠️ AVISO: Erro ao buscar TabNews: {e}")

    # 2. Dev.to API (Global)
    try:
        url = "https://dev.to/api/articles?top=1&per_page=3"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            articles = res.json()
            for a in articles:
                items.append({
                    "fonte": "Dev.to (Global)",
                    "titulo": a.get("title", ""),
                    "resumo": f"Tags: {', '.join(a.get('tag_list', []))}"
                })
    except Exception as e:
        print(f"  ⚠️ AVISO: Erro ao buscar Dev.to: {e}")

    print(f"  ✅ {len(items)} noticias/tendencias encontradas.")
    return items


def fetch_personal_knowledge():
    """Busca registros da Base Pessoal do Notion via REST API direta (estavel)."""
    print("🧠 Coletando insumos da sua Base Pessoal no Notion...")
    if not NOTION_KEY or not BASE_DB_ID:
        print("  ⚠️ Notion key ou Base DB ID ausentes.")
        return []

    headers = {
        "Authorization": f"Bearer {NOTION_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    url = f"https://api.notion.com/v1/databases/{BASE_DB_ID}/query"
    personal_items = []

    try:
        res = requests.post(url, headers=headers, json={"page_size": 10}, timeout=10)
        
        if res.status_code == 200:
            pages = res.json().get("results", [])

            for p in pages:
                props = p.get("properties", {})
                
                # Titulo
                title_objs = props.get("Título", {}).get("title", [])
                title = title_objs[0].get("plain_text", "") if title_objs else ""
                
                # Tipo
                tipo_obj = props.get("Tipo", {}).get("select")
                tipo = tipo_obj.get("name", "Geral") if tipo_obj else "Geral"
                
                # Descricao
                desc_objs = props.get("Descrição", {}).get("rich_text", [])
                desc = desc_objs[0].get("plain_text", "") if desc_objs else ""
                
                # Usado
                usado = props.get("Usado em post?", {}).get("checkbox", False)

                if not usado and title:
                    personal_items.append({
                        "titulo": title,
                        "tipo": tipo,
                        "descricao": desc
                    })

            print(f"  ✅ {len(personal_items)} experiencia(s) pessoal(is) nao utilizada(s) encontrada(s).")
        else:
            print(f"  ❌ Erro ao consultar Notion (HTTP {res.status_code}): {res.text}")

        return personal_items

    except Exception as e:
        print(f"  ❌ Erro ao consultar Base Pessoal no Notion: {e}")
        return []


def get_full_context():
    """Junta o contexto externo (noticias) + interno (experiencias reais)."""
    external = fetch_external_news()
    personal = fetch_personal_knowledge()
    
    return {
        "external_news": external,
        "personal_experiences": personal
    }


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 TESTANDO COLETOR DE CONTEXTO DO AGENTE")
    print("=" * 60)
    ctx = get_full_context()
    
    print("\n📰 NOTICIAS EXTERNAS COLETADAS:")
    for n in ctx["external_news"]:
        print(f"  • [{n['fonte']}] {n['titulo']}")
        
    print("\n💡 EXPERIENCIAS PESSOAIS NO NOTION:")
    if ctx["personal_experiences"]:
        for p in ctx["personal_experiences"]:
            print(f"  • [{p['tipo']}] {p['titulo']}: {p['descricao']}")
    else:
        print("  (Nenhuma anotação nova na sua Base Pessoal do Notion. Tudo pronto!)")
    print("=" * 60)