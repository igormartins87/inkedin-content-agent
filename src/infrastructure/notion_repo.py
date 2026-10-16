import requests
import unicodedata
from datetime import datetime, timedelta
from src.domain.interfaces import INotionRepository
from src.domain.models import PostDraft
from src.config.settings import settings

class NotionRepository(INotionRepository):
    def __init__(self):
        self.token = settings.NOTION_TOKEN
        self.db_ideas_id = settings.NOTION_DATABASE_IDEAS_ID
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

    def _normalize(self, s: str) -> str:
        return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII').lower().strip()

    def _build_select_payload(self, prop_def: dict, desired_name: str):
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

    def cleanup_old_posts(self, days: int = 30) -> int:
        print(f"🧹 Verificando e limpando posts com mais de {days} dias no Notion...", flush=True)
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        url = f"https://api.notion.com/v1/databases/{self.db_ideas_id}/query"
        payload = {"filter": {"property": "Data de criação", "date": {"before": cutoff_date}}}
        
        try:
            r = requests.post(url, headers=self.headers, json=payload, timeout=20)
            if r.status_code == 200:
                results = r.json().get("results", [])
                archived = 0
                for page in results:
                    p_url = f"https://api.notion.com/v1/pages/{page['id']}"
                    patch = requests.patch(p_url, headers=self.headers, json={"archived": True}, timeout=15)
                    if patch.status_code == 200:
                        archived += 1
                print(f"  🗑️ {archived} post(s) antigo(s) arquivado(s).", flush=True)
                return archived
        except Exception as e:
            print(f"⚠️ Erro na limpeza do Notion: {e}")
        return 0

    def save_post(self, post: PostDraft) -> bool:
        self.cleanup_old_posts(days=30)
        
        schema_url = f"https://api.notion.com/v1/databases/{self.db_ideas_id}"
        r = requests.get(schema_url, headers=self.headers, timeout=20)
        if r.status_code != 200:
            print(f"❌ Erro ao ler schema do Notion ({r.status_code}): {r.text}")
            return False

        schema_props = r.json().get("properties", {})
        map_names = {}
        for real_name, prop in schema_props.items():
            norm = self._normalize(real_name)
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

        payload_props = {}
        today_str = datetime.now().strftime("%Y-%m-%d")

        if "title" in map_names:
            payload_props[map_names["title"]] = {"title": [{"text": {"content": post.title[:100]}}]}
        if "pilar" in map_names and map_names["pilar"] in schema_props:
            payload = self._build_select_payload(schema_props[map_names["pilar"]], post.pillar)
            if payload:
                payload_props[map_names["pilar"]] = payload
        if "formato" in map_names and map_names["formato"] in schema_props:
            payload = self._build_select_payload(schema_props[map_names["formato"]], post.suggested_format)
            if payload:
                payload_props[map_names["formato"]] = payload
        if "status" in map_names and map_names["status"] in schema_props:
            payload = self._build_select_payload(schema_props[map_names["status"]], "💡 Ideia / Rascunho")
            if payload:
                payload_props[map_names["status"]] = payload
        if "rascunho" in map_names:
            chunks = [post.content[i:i+1900] for i in range(0, len(post.content), 1900)] or [""]
            payload_props[map_names["rascunho"]] = {"rich_text": [{"text": {"content": c}} for c in chunks]}
        if "data" in map_names:
            payload_props[map_names["data"]] = {"date": {"start": today_str}}

        url = "https://api.notion.com/v1/pages"
        print(f"📝 Salvando no Notion: '{post.title}'...", flush=True)
        try:
            resp = requests.post(url, headers=self.headers, json={"parent": {"database_id": self.db_ideas_id}, "properties": payload_props}, timeout=20)
            if resp.status_code == 200:
                print("  ✅ Salvo no Notion com sucesso!", flush=True)
                return True
            else:
                print(f"  ❌ Resposta da API do Notion ({resp.status_code}): {resp.text}", flush=True)
                return False
        except Exception as e:
            print(f"❌ Erro de conexão ao salvar no Notion: {e}")
            return False