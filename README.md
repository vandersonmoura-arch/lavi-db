# Agente Whatsapp com IA - Barbearia LaVi

Agente de atendimento automatizado via WhatsApp, com memoria de conversa persistente e inteligencia artificial.

O cliente manda mensagem no WhatsApp, o agente responde com informacoes reais do negocio e nunca inventa dados.

## Arquitetura

Cliente (WhatsApp)
|
Evolution API (webhook)
|
FastAPI (Railway)
|--- Gemini API (resposta)
|--- PostgreSQL / Supabase (historico)
|
Evolution API (envia resposta)
|
Cliente (WhatsApp)


## Funcionalidades

- Atendimento automatico via WhatsApp
- Memoria de conversa por cliente (identificado por telefone)
- Historico persistente em PostgreSQL (Supabase)
- System prompt com informacoes reais do negocio
- Tratamento de erros com mensagem amigavel ao cliente
- Logs estruturados com data, hora e nivel
- Protecao contra loop (ignora mensagens do proprio agente)
- Suporte a mensagens simples e extendedTextMessage
- Deploy continuo via GitHub + Railway

## Tecnologias

- Python 3.12
- FastAPI
- Google Gemini API
- PostgreSQL (Supabase)
- Evolution API v2.3
- Railway (deploy)

## Endpoints

| Metodo | Rota | Descricao |
| --- | --- | --- |
| GET | / | Verifica se o agente esta no ar |
| POST | /conversar | Envia mensagem via API (Swagger) |
| POST | /whatsapp | Webhook do Evolution API |

## Variaveis de ambiente

| Nome | Descricao |
| --- | --- |
| GEMINI_API_KEY | Chave da API do Google Gemini |
| EVOLUTION_API_KEY | Chave da instancia no Evolution |
| EVOLUTION_URL | Endereco do servidor Evolution |
| DATABASE_URL | Conexao PostgreSQL (Supabase) |

## Como rodar localmente

```bash
pip install -r requirements.txt
```

Crie um arquivo .env com as variaveis acima.

```bash
uvicorn agente:app --reload
```

Acesse a documentacao em http://127.0.0.1:8000/docs

## Estrutura