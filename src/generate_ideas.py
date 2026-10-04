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

def get_active_models(client):
    """Consulta os modelos de texto ativos na conta Groq."""
    preferred = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant"
    ]
    try:
        models_page = client.models.list()
        all_ids = [m.id for m in models_page.data]
        
        # Filtra apenas modelos de texto válidos
        ignore_keywords = ["guard", "whisper", "vision", "audio", "orpheus", "allam", "safeguard", "embed"]
        valid = [
            m_id for m_id in all_ids 
            if not any(k in m_id.lower() for k in ignore_keywords)
        ]
        
        ordered = [p for p in preferred if p in valid]
        for v in valid:
            if v not in ordered:
                ordered.append(v)
        return ordered if ordered else all_ids
    except Exception as e:
        print(f"⚠️ Erro ao listar modelos do Groq: {e}", flush=True)
        return preferred

SYSTEM_PROMPT = """
Você é um Ghostwriter especialista em LinkedIn para Desenvolvedores de Software e Profissionais de Tecnologia.
Sua missão é gerar 3 rascunhos de posts em Português (PT-BR), escritos em 1ª pessoa do singular ("eu"), aplicando uma estrutura rigorosa de copywriting e alto engajamento.

### REGRAS OBRIGATÓRIAS DE ESTRUTURA PARA CADA POST:
1. **Gancho 1:** Frase curta, impactante e direta que atrai a atenção do leitor. NUNCA comece com uma pergunta.
2. **Gancho 2:** Frase curta na linha seguinte que estabelece o contexto do post.
3. **Corpo do Post:** 
   - Preencha uma lacuna de conhecimento de forma extremamente didática e simples (passo a passo em etapas distintas).
   - Escreva novas frases em novas linhas (quebras de linha frequentes para facilitar a leitura no celular).
   - Linguagem acessível, fluida, humana e natural. Evite jargões complexos desnecessários.
4. **Penúltima frase:** Uma afirmação contundente que reforça uma crença forte e compartilhada da comunidade dev.
5. **Última frase (CTA):** Um convite à interação incentivando os leitores a comentarem algo que eles realmente queiram compartilhar.

### BANLIST E REGRAS DE ESTILO (HUMANIZAÇÃO):
- NUNCA use as palavras/expressões proibidas: "no mundo dinâmico de hoje", "revolucionar", "alavancar", "divisor de águas", "no ecossistema atual", "desvendar", "mergulhar fundo", "em suma", "vamos lá".
- Proibido uso excessivo de emojis (máximo 1 ou 2 por post inteiro).
- Proibido hashtags em excesso (máximo 3 no final).

### FORMATO DE SAÍDA EM JSON:
Você DEVE responder EXCLUSIVAMENTE em formato JSON contendo a chave "posts" com uma lista de 3 objetos:
{
  "posts": [
    {
      "titulo_ideia": "Título curto da ideia 1",
      "pilar": "Dev & Código",
      "formato": "Tutorial / Dica Prática",
      "conteudo_post": "Texto completo do post 1..."
    },
    {
      "titulo_ideia": "Título curto da ideia 2",
      "pilar": "Carreira & Mercado",
      "formato": "Análise / Opinião",
      "conteudo_post": "Texto completo do post 2..."
    },
    {
      "titulo_ideia": "Título curto da ideia 3",
      "pilar": "Tendências & IA",
      "formato": "Storytelling / Experiência",
      "conteudo_post": "Texto completo do post 3..."
    }
  ]
}
"""

def parse_response_to_ideas(raw_text):
    """Tenta converter a resposta da IA em lista de posts com múltiplos fallbacks."""
    if not raw_text or not raw_text.strip():
        return []
        
    cleaned = raw_text.strip()
    
    # Limpa blocos de código Markdown
    if "```" in cleaned:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if match:
            cleaned = match.group(1).strip()
        else:
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    # Tentativa 1: Parse direto do JSON
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            if "posts" in data and isinstance(data["posts"], list):
                return data["posts"]
            elif "ideias" in data and isinstance(data["ideias"], list):
                return data["ideias"]
            else:
                return [data]
        elif isinstance(data, list):
            return data
    except Exception:
        pass

    # Tentativa 2: Buscar JSON usando regex para encontrar { ... } ou [ ... ]
    json_match = re.search(r"(\[[\s\S]*\]|\{[\s\S]*\})", cleaned)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            if isinstance(data, dict):
                if "posts" in data:
                    return data["posts"]
                return [data]
            elif isinstance(data, list):
                return data
        except Exception:
            pass

    # Tentativa 3 (Fallback de emergência): Se veio texto puro, encapsula como um post para não perder o conteúdo
    lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
    first_line = lines[0] if lines else "Post Gerado pela IA"
    title = first_line.replace("#", "").replace("*", "").strip()[:60]
    
    return [{
        "titulo_ideia": title,
        "pilar": "Dev & Código",
        "formato": "Tutorial / Dica Prática",
        "conteudo_post": cleaned
    }]

def generate_ideas():
    print("🔍 Coletando contexto (Notion + Notícias)...", flush=True)
    context = get_full_context()

    user_prompt = f"""
    Com base no contexto atual coletado abaixo, gere 3 posts de altíssimo engajamento seguindo a estrutura do sistema.

    ### CONTEXTO DA SEMANA:
    {json.dumps(context, ensure_ascii=False, indent=2)}

    Retorne a resposta EXCLUSIVAMENTE em formato JSON com 3 posts na chave 'posts'.
    """

    candidate_models = get_active_models(client)

    for model_name in candidate_models:
        print(f"🤖 Gerando postagens com o modelo Groq: {model_name}...", flush=True)
        
        # Tenta primeiro com JSON mode e depois sem
        for try_json_mode in [True, False]:
            try:
                kwargs = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 3000
                }
                if try_json_mode:
                    kwargs["response_format"] = {"type": "json_object"}

                response = client.chat.completions.create(**kwargs)
                raw_text = response.choices[0].message.content.strip()
                
                if raw_text and len(raw_text) > 30:
                    ideas = parse_response_to_ideas(raw_text)
                    if ideas:
                        print(f"✅ Sucesso! {len(ideas)} postagem(ns) gerada(s) com o modelo: {model_name}", flush=True)
                        return ideas
            except Exception:
                continue

    raise RuntimeError("❌ Nenhum modelo do Groq conseguiu retornar um resultado válido.")

if __name__ == "__main__":
    ideas = generate_ideas()
    print(f"\n✅ {len(ideas)} Ideias geradas com sucesso!\n", flush=True)
    print(json.dumps(ideas, ensure_ascii=False, indent=2))