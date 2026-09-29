import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

print("=" * 60)
print("🚀 DIAGNOSTICO DEFINITIVO (V9) - VALIDACAO DE CONEXOES")
print("=" * 60)

if not ENV_PATH.exists():
    print(f"❌ ERRO CRITICO: Arquivo .env nao encontrado em {ENV_PATH}")
    sys.exit(1)

# Leitura e sanitização do .env
raw_bytes = ENV_PATH.read_bytes()
if raw_bytes.startswith(b'\xef\xbb\xbf'):
    raw_bytes = raw_bytes[3:]
    ENV_PATH.write_bytes(raw_bytes)

env_vars = {}
for line in raw_bytes.decode('utf-8', errors='ignore').splitlines():
    line = line.strip()
    if not line or line.startswith('#') or '=' not in line:
        continue
    k, v = line.split('=', 1)
    env_vars[k.strip().replace('\ufeff', '')] = v.strip().strip('"').strip("'").replace('\ufeff', '')

GROQ_KEY = env_vars.get("GROQ_API_KEY", "")
NOTION_KEY = env_vars.get("NOTION_API_KEY", "")

# IDs REAIS descobertos pelo script na pagina do Notion
IDEIAS_ID = "3de714ac-461f-80e5-af97-c64de001aede"
BASE_ID = "3de714ac-461f-809c-be51-e509bf4336bc"

# 1. Teste do Notion com .retrieve()
def test_notion():
    from notion_client import Client
    print("\n📚 1. TESTANDO CONEXAO COM AS DATABASES DO NOTION...")
    if not NOTION_KEY:
        print("  ❌ NOTION_API_KEY ausente.")
        return False

    notion = Client(auth=NOTION_KEY)
    success = True

    try:
        db1 = notion.databases.retrieve(database_id=IDEIAS_ID)
        t1 = db1.get("title", [{}])[0].get("plain_text", "Ideias de Post")
        print(f"  ✅ Database 1 ACESSADA: '{t1}' | ID: {IDEIAS_ID}")
    except Exception as e:
        print(f"  ❌ Erro na Database Ideias: {e}")
        success = False

    try:
        db2 = notion.databases.retrieve(database_id=BASE_ID)
        t2 = db2.get("title", [{}])[0].get("plain_text", "Base de Conhecimento Pessoal")
        print(f"  ✅ Database 2 ACESSADA: '{t2}' | ID: {BASE_ID}")
    except Exception as e:
        print(f"  ❌ Erro na Database Base Pessoal: {e}")
        success = False

    return success

# 2. Teste do Groq varrendo modelos ativos
def test_groq():
    from groq import Groq
    print("\n🤖 2. TESTANDO INFERENCIA NA API DO GROQ...")
    if not GROQ_KEY:
        print("  ❌ GROQ_API_KEY ausente.")
        return None

    try:
        client = Groq(api_key=GROQ_KEY)
        models_data = client.models.list().data
        model_ids = [m.id for m in models_data if m.id]
        
        print(f"  🔎 Testando {len(model_ids)} modelos disponiveis na sua conta...")
        
        working_model = None
        for m_id in model_ids:
            # Ignora modelos que nao sao para geracao de texto
            if any(x in m_id.lower() for x in ['guard', 'whisper', 'embed']):
                continue
            try:
                res = client.chat.completions.create(
                    messages=[{"role": "user", "content": "Responda apenas: OK"}],
                    model=m_id
                )
                msg = res.choices[0].message.content.strip()
                print(f"  ✅ MODELO ATIVO ENCONTRADO: '{m_id}' (Resposta: {msg})")
                working_model = m_id
                break
            except Exception:
                continue

        if not working_model:
            print("  ❌ Nenhum modelo de chat respondeu com sucesso.")
            
        return working_model

    except Exception as e:
        print(f"  ❌ Erro ao conectar no Groq: {e}")
        return None

# 3. Atualizar arquivo .env
def update_env(working_model):
    print("\n💾 3. GRAVANDO CONFIGURACOES CORRETAS NO ARQUIVO .ENV...")
    env_vars["NOTION_DATABASE_IDEIAS_ID"] = IDEIAS_ID
    env_vars["NOTION_DATABASE_BASE_ID"] = BASE_ID
    if working_model:
        env_vars["GROQ_MODEL"] = working_model
        
    lines = [f"{k}={v}" for k, v in env_vars.items()]
    ENV_PATH.write_text("\n".join(lines), encoding="utf-8")
    print("  🎉 ARQUIVO .ENV ATUALIZADO COM SUCESSO!")

if __name__ == "__main__":
    notion_ok = test_notion()
    groq_model = test_groq()
    
    if notion_ok:
        update_env(groq_model)
        
    print("\n" + "=" * 60)
    if notion_ok and groq_model:
        print("🚀 SUCESSO ABSOLUTO: TODAS AS CONEXOES ESTAO 100% OPERACIONAIS!")
    else:
        print("⚠️ Verifique os logs acima para ajustes finos.")
    print("=" * 60)