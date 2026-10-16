import json
import re
import time
from groq import Groq, RateLimitError
from src.domain.interfaces import ILLMProvider
from src.domain.models import WeeklyContext, PostDraft
from src.config.settings import settings

class GroqLLMProvider(ILLMProvider):
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("❌ GROQ_API_KEY ausente!")
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def _get_active_models(self) -> list[str]:
        preferred = ["llama-3.1-8b-instant", "qwen/qwen3.8-27b", "openai/gpt-oss-120b", "llama-3.3-70b-versatile"]
        try:
            models_page = self.client.models.list()
            available = [m.id for m in models_page.data]
            ordered = [p for p in preferred if p in available]
            for m in available:
                if m not in ordered and not any(x in m for x in ["guard", "whisper", "vision", "audio"]):
                    ordered.append(m)
            return ordered if ordered else ["llama-3.1-8b-instant"]
        except Exception:
            return ["llama-3.1-8b-instant", "qwen/qwen3.8-27b"]

    def _call_with_fallback(self, candidate_models: list[str], system_prompt: str, user_prompt: str) -> str:
        for model in candidate_models:
            try:
                res = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=800  # Ajustado para respeitar a quota gratuita de OTPM do Groq
                )
                text = res.choices[0].message.content.strip()
                if text:
                    return text
            except RateLimitError:
                print(f"⚠️ Limite de cota no modelo {model}. Tentando o próximo modelo...", flush=True)
                time.sleep(1)
            except Exception as e:
                print(f"⚠️ Erro no modelo {model}: {e}. Tentando o próximo...", flush=True)
        raise RuntimeError("❌ Todos os modelos do Groq falharam ou atingiram o limite de taxa.")

    def generate_post(self, context: WeeklyContext) -> PostDraft:
        candidate_models = self._get_active_models()
        print(f"🤖 Usando esteira de 3 etapas com fallback de modelos no Groq...", flush=True)

        context_dict = {
            "noticias": [{"titulo": n.title, "fonte": n.source} for n in context.news],
            "experiencias_pessoais": [{"titulo": k.title, "descricao": k.description} for k in context.personal_knowledge]
        }

        # Etapa 1: Rascunho com Gancho Duplo
        print(" ➔ [Etapa 1/3] Criando rascunho com Gancho Duplo...", flush=True)
        sys_1 = "Ghostwriter especialista em LinkedIn para Devs. Crie 1 post em PT-BR (1ª pessoa). REGRAS: 1) Gancho 1 curto sem pergunta. 2) Gancho 2 de contexto. 3) Corpo em passos separados por quebra de linha. 4) Penúltima frase: crença forte dev. 5) Última frase: convite para comentário real."
        draft_1 = self._call_with_fallback(candidate_models, sys_1, f"CONTEXTO DA SEMANA:\n{json.dumps(context_dict, ensure_ascii=False)}")

        time.sleep(2)  # Pausa de segurança para não estourar tokens/minuto

        # Etapa 2: Simplificação Didática
        print(" ➔ [Etapa 2/3] Simplificando linguagem para iniciantes...", flush=True)
        sys_2 = "Editor de clareza. Mantenha facílima para iniciante em tech. Sem jargões pesados ou palavras como 'dados geofísicos'. Remova TODOS os títulos de seções/marcações. Mantenha quebras de linha."
        draft_2 = self._call_with_fallback(candidate_models, sys_2, f"TEXTO PARA SIMPLIFICAR:\n{draft_1}")

        time.sleep(2)  # Pausa de segurança

        # Etapa 3: Polimento Final e JSON
        print(" ➔ [Etapa 3/3] Lapidando estilo e formatando JSON final...", flush=True)
        sys_3 = "Consultor de marca pessoal dev. Refine para tom autêntico e natural. Remova clichês de IA. Retorne EXCLUSIVAMENTE um JSON: {\"titulo_ideia\": \"...\", \"pilar\": \"Dev & Código\", \"formato\": \"Tutorial / Dica Prática\", \"conteudo_post\": \"...\"}"
        final_raw = self._call_with_fallback(candidate_models, sys_3, f"TEXTO PARA REFINAR:\n{draft_2}")

        if "```" in final_raw:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", final_raw)
            final_raw = match.group(1).strip() if match else final_raw.replace("```json", "").replace("```", "").strip()

        try:
            data = json.loads(final_raw)
            return PostDraft(
                title=data.get("titulo_ideia", "Post da Semana"),
                pillar=data.get("pilar", "Dev & Código"),
                suggested_format=data.get("formato", "Tutorial / Dica Prática"),
                content=data.get("conteudo_post", draft_2)
            )
        except Exception:
            return PostDraft(
                title="Post da Semana (Refinado)",
                pillar="Dev & Código",
                suggested_format="Tutorial / Dica Prática",
                content=draft_2
            )