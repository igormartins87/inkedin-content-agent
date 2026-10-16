import requests
from src.domain.interfaces import IContextCollector
from src.domain.models import WeeklyContext, TechNews, KnowledgeItem
from src.config.settings import settings

class ContextAggregatorCollector(IContextCollector):
    def fetch_context(self) -> WeeklyContext:
        print("🔍 Coletando contexto da semana (Notion + TabNews + Dev.to)...", flush=True)
        news = self._fetch_tabnews() + self._fetch_devto()
        knowledge = self._fetch_notion_knowledge()
        return WeeklyContext(news=news, personal_knowledge=knowledge)

    def _fetch_tabnews(self) -> list[TechNews]:
        url = "https://www.tabnews.com.br/api/v1/contents?page=1&per_page=5&strategy=relevant"
        items = []
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                for item in r.json():
                    slug = item.get('slug')
                    owner = item.get('owner_username')
                    link = f"https://www.tabnews.com.br/{owner}/{slug}" if slug and owner else "https://www.tabnews.com.br"
                    items.append(TechNews(title=item.get("title", ""), source="TabNews", url=link))
        except Exception as e:
            print(f"⚠️ Erro TabNews: {e}")
        return items

    def _fetch_devto(self) -> list[TechNews]:
        url = "https://dev.to/api/articles?top=1&per_page=3"
        items = []
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                for item in r.json():
                    items.append(TechNews(title=item.get("title", ""), source="Dev.to", url=item.get("url", "")))
        except Exception as e:
            print(f"⚠️ Erro Dev.to: {e}")
        return items

    def _fetch_notion_knowledge(self) -> list[KnowledgeItem]:
        if not settings.NOTION_TOKEN or not settings.NOTION_DATABASE_KNOWLEDGE_ID:
            return []
        url = f"https://api.notion.com/v1/databases/{settings.NOTION_DATABASE_KNOWLEDGE_ID}/query"
        headers = {
            "Authorization": f"Bearer {settings.NOTION_TOKEN}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        payload = {"filter": {"property": "Usado em post?", "checkbox": {"equals": False}}}
        items = []
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=15)
            if r.status_code == 200:
                for page in r.json().get("results", []):
                    props = page.get("properties") or {}
                    
                    titulo_prop = props.get("Título") or props.get("Titulo") or {}
                    title_objs = titulo_prop.get("title") or []
                    title = title_objs[0].get("plain_text", "") if title_objs else ""
                    
                    desc_prop = props.get("Descrição") or props.get("Descricao") or {}
                    desc_objs = desc_prop.get("rich_text") or []
                    desc = desc_objs[0].get("plain_text", "") if desc_objs else ""
                    
                    tipo_prop = props.get("Tipo") or {}
                    select_obj = tipo_prop.get("select") or {}
                    type_tag = select_obj.get("name", "Geral")
                    
                    if title:
                        items.append(KnowledgeItem(id=page["id"], title=title, description=desc, type_tag=type_tag))
        except Exception as e:
            print(f"⚠️ Erro Notion Knowledge: {e}")
        return items