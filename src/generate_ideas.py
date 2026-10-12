import os
import sys
import json
import re
from pathlib import Path
from groq import Groq

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from fetch_context import get_full_context

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

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY não encontrada no arquivo .env!")

client = Groq(api_key=GROQ_API_KEY)

def get_best_model(client):
    """Retorna o melhor modelo de texto ativo na conta Groq."""
    preferred = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant"
    ]
    try:
        models_page = client.models.list()
        available = [m.id for m in models_page.data]
        for p in preferred:
            if p in available:
                return p
        # Se não achou preferencial, pega o primeiro de texto válido
        valid = [m for m in available if not any(x in m for x in ["guard", "whisper", "vision", "audio"])]
        return valid[0] if valid else "qwen/qwen3.8-27b"
    except Exception:
        return "qwen/qwen3.8-27b"

def call_groq(model_name, system_prompt, user_prompt):
    """Executa uma chamada ao Groq com tratamento de erro."""
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=2500
    )
    return response.choices[0].message.content.strip()

def generate_ideas():
    print("🔍 Coletando contexto da semana (Notion + Notícias)...", flush=True)
    context = get_full_context()
    model = get_best_model(client)
    print(f"🤖 Usando o modelo Groq ({model}) na esteira de 3 etapas de refinamento...", flush=True)

    # =========================================================================
    # ETAPA 1: CRIAÇÃO DO RASCUNHO BASE (ESTRUTURA DE ENGAJAMENTO)
    # =========================================================================
    print(" ➔ [Etapa 1/3] Criando rascunho com Gancho Duplo e Estrutura de Engajamento...", flush=True)
    
    system_prompt_1 = """
    Você é um Ghostwriter especialista em LinkedIn para Desenvolvedores de Software.
    Sua missão é selecionar o melhor assunto do contexto e criar 1 post em Português (PT-BR), em 1ª pessoa ("eu").

    REGRAS DE ESTRUTURA OBRIGATÓRIAS:
    1. Gancho 1: Frase curta, impactante e direta que atrai a atenção. NUNCA comece com uma pergunta.
    2. Gancho 2: Frase curta na linha seguinte estabelecendo o contexto.
    3. Corpo: Preencha uma lacuna de conhecimento ajudando as pessoas em etapas distintas (passo a passo em linhas separadas com quebra de linha).
    4. Penúltima frase: Uma afirmação contundente que reforça uma crença forte do público dev.
    5. Última frase: Um convite à interação incentivando comentários que as pessoas queiram compartilhar.
    """

    user_prompt_1 = f"CONTEXTO DA SEMANA:\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\nEscreva a primeira versão do post."
    draft_1 = call_groq(model, system_prompt_1, user_prompt_1)

    # =========================================================================
    # ETAPA 2: SIMPLIFICAÇÃO DIDÁTICA E REMOÇÃO DE TÍTULOS
    # =========================================================================
    print(" ➔ [Etapa 2/3] Simplificando linguagem para iniciantes e removendo títulos de seções...", flush=True)
    
    system_prompt_2 = """
    Você é um editor de texto especialista em clareza e didática.
    MUDE O TEXTO RECEBIDO SEGUINDO ESTAS REGRAS:
    1. Deixe de facílima compreensão para quem está iniciando na área de tecnologia.
    2. NUNCA use termos desnecessariamente complexos ou termos como "dados geofísicos", "ecossistema dinâmico", "paradigma", etc.
    3. Remova COMPLETAMENTE qualquer título de seção ou marcação (ex: não use "Gancho 1:", "Corpo:", "Etapa 1:", "Conclusão:").
    4. Mantenha a estrutura em quebras de linha frequentes.
    """

    user_prompt_2 = f"TEXTO PARA SIMPLIFICAR:\n{draft_1}"
    draft_2 = call_groq(model, system_prompt_2, user_prompt_2)

    # =========================================================================
    # ETAPA 3: REFINAMENTO DE ESTILO, FLUIDEZ E VERSÃO PRONTA PARA POSTAR
    # =========================================================================
    print(" ➔ [Etapa 3/3] Lapidando estilo, fluidez e gerando a versão final pronta para postar...", flush=True)

    system_prompt_3 = """
    Você é um consultor de marca pessoal de tecnologia.
    Sua missão é fazer a revisão final do post.

    REGRAS DE REFINAMENTO FINAL:
    1. Refine o texto para combinar com um tom humano, autêntico e natural de um desenvolvedor experiente.
    2. Qualquer parte que não parecer fluir bem conceitualmente, reescreva para soar fluida e envolvente.
    3. Remova qualquer jargão corporativo ou clichê artificial de IA ("no mundo dinâmico de hoje", "revolucionar", "alavancar", "vamos lá").
    4. Entregue o texto final 100% PRONTO PARA PUBLICAR NO LINKEDIN.

    FORMATO DE SAÍDA:
    Retorne EXCLUSIVAMENTE um objeto JSON com o formato:
    {
      "titulo_ideia": "Título curto sobre o tema para identificação interna",
      "pilar": "Dev & Código",
      "formato": "Tutorial / Dica Prática",
      "conteudo_post": "Texto completo refinado pronto para publicar..."
    }
    """

    user_prompt_3 = f"TEXTO PARA REFINAR E ENTREGAR VERSÃO PRONTA:\n{draft_2}\n\nRetorne apenas o JSON puro."
    
    try:
        final_json_raw = call_groq(model, system_prompt_3, user_prompt_3)
        if "```" in final_json_raw:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", final_json_raw)
            final_json_raw = match.group(1).strip() if match else final_json_raw.replace("```json", "").replace("```", "").strip()

        final_data = json.loads(final_json_raw)
        return [final_data]
    except Exception as e:
        print(f"⚠️ Erro ao estruturar JSON final: {e}. Usando fallback limpo.")
        return [{
            "titulo_ideia": "Post da Semana (Refinado)",
            "pilar": "Dev & Código",
            "formato": "Tutorial / Dica Prática",
            "conteudo_post": draft_2
        }]

if __name__ == "__main__":
    ideas = generate_ideas()
    print(f"\n✅ Post final lapidado e pronto para publicação!\n", flush=True)
    print(json.dumps(ideas, ensure_ascii=False, indent=2))