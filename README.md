# 🎯 LinkedIn Content Agent — Agente Autônomo de Conteúdo com IA & Clean Architecture

[![Python 3.11](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Clean%20%2F%20SOLID-emerald.svg)]()
[![Automation](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-purple.svg)](https://github.com/features/actions)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Agente Serverless 100% Autônomo** que realiza curadoria de tendências de mercado, combina com histórico do usuário e gera semanalmente postagens humanizadas de alto engajamento para o LinkedIn usando **Prompt Chaining em 3 Etapas (LLMs)**, **Notion REST API** e **Gmail SMTP**.

---

## 💡 O Problema vs. A Solução

### 🔴 O Problema
Criar conteúdo estratégico e frequente para o LinkedIn exige entre **3 a 5 horas semanais** divididas entre pesquisa de tendências, redação de ganchos de atração, revisão de tom de voz e formatação. Para profissionais e empresas, manter essa consistência sem perder o foco na operação é um grande desafio.

### 🟢 A Solução
O **LinkedIn Content Agent** elimina 100% do trabalho operacional:
* 📡 **Coleta Notícias & Experiências:** Monitora APIs tech (TabNews, Dev.to) e extrai vivências registradas no Notion.
* 🤖 **Prompt Chaining (IA em 3 Etapas):** Emprega uma esteira de LLMs no Groq (Llama 3.1 / Qwen 2.5) que gera o rascunho, simplifica jargões complexos e aplica humanização sem "clichês de IA".
* 📥 **Gestão & Limpeza no Notion:** Organiza os rascunhos em um banco de dados e executa **auto-cleanup** de posts com mais de 30 dias.
* 📧 **Alerta por E-mail:** Notifica o criador no domingo à noite com o post pronto para revisão e publicação em 1 clique.
* 💰 **Custo Zero ($0/mês):** Executado em infraestrutura Serverless no GitHub Actions.

---

## 🏛️ Arquitetura de Software & Princípios SOLID

Este projeto foi desenvolvido seguindo os princípios da **Clean Architecture** para garantir testabilidade, desacoplamento e facilidade de manutenção.

```text
src/
├── config/             # Configurações centralizadas e tratamento de ambiente (.env / BOM)
│   └── settings.py
├── domain/             # Entidades puras e Interfaces (Contratos do Sistema)
│   ├── interfaces.py   # Interfaces abstratas (DIP / ISP)
│   └── models.py       # Dataclasses de domínio (PostDraft, WeeklyContext, etc.)
├── infrastructure/     # Adaptadores de Entrada/Saída (I/O & APIs de Terceiros)
│   ├── collectors.py   # Coletor de tendências (TabNews, Dev.to) e Notion Knowledge
│   ├── llm_provider.py # Provider Groq com Fallback e Esteira de Refinamento
│   ├── notion_repo.py  # Repositório Notion (CRUD + Auto-Cleanup > 30 dias)
│   └── gmail_notifier.py # Serviço de envio SMTP do Gmail
├── use_cases/          # Regras de Negócio de Alto Nível
│   └── generate_weekly_post.py
└── main.py             # Entrypoint & Injeção de Dependências (DI Container)

