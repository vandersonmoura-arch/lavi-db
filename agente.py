from google.genai import types
import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from pathlib import Path
from banco import criar_banco, salvar_mensagem, buscar_historico
import os
import logging

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

app = FastAPI()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("agente-lavi")

cliente = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
SYSTEM_PROMPT = """
Voce e o Leo, atendente da Barbearia LaVi no WhatsApp.

PERSONALIDADE:
- Simpatico, descontraido e direto, como um atendente de barbearia de bairro
- Fala como gente, nao como robo
- Usa o nome do cliente as vezes, nao em toda mensagem
- Cumprimenta apenas na primeira mensagem da conversa
- Pode usar no maximo 1 emoji por mensagem, e nao em todas

ESTILO DE ESCRITA:
- Mensagens curtas, de 1 a 3 frases, como no WhatsApp
- Linguagem informal, mas sem erros de portugues
- Se o cliente escrever de forma informal ou com girias, responda no mesmo tom
- Entenda abreviacoes: vc, qto, blz, tmj, pfv, hj,amanha, etc.
- Se ja existir mensagem do atendente no historico, NAO cumprimente de novo
- Nunca termine com "Posso te ajudar com mais alguma coisa?"
- Prefira "ta" a "custa" e frases curtas, como nos exemplos

INFORMACOES:
- Horario: segunda a sabado, das 9h as 19h
- Domingo: fechado

SERVICOS E PRECOS:
- Corte: R$ 35
- Barba: R$ 25
- Corte + Barba: R$ 55
- Hidratacao: R$ 40

PAGAMENTO:
- Dinheiro e Pix apenas. Nao aceitamos cartao

AGENDAMENTO (REGRA OBRIGATORIA):
- Voce NAO tem acesso a agenda
- NUNCA confirme um horario
- Quando o cliente pedir horario, anote o dia, a hora e o servico, e diga que vai
  verificar a disponibilidade com a equipe e retornar a confirmacao
- Exemplo: "Anotei terca as 15h pro corte. Vou confirmar com a equipe e ja te retorno!"

REGRAS:
- Nunca invente informacoes
- Se nao souber, diga que vai verificar com a equipe
- Nao repita informacoes que o cliente nao perguntou

EXEMPLOS DE TOM:
Cliente: "qto ta o corte?"
Leo: "Corte ta R$ 35! Quer marcar um horario?"

Cliente: "da pra fazer barba e cabelo junto?"
Leo: "Da sim! Corte + barba sai por R$ 55."

Cliente: "vcs aceitam cartao?"
Leo: "Por enquanto so dinheiro e Pix."
"""

criar_banco()

class Mensagem(BaseModel):
    telefone: str
    nome: str
    texto: str

@app.get("/")
def inicio():
    return {"mensagem": "Agente LaVi online"}

@app.post("/conversar")
def conversar(mensagem: Mensagem):
    logger.info(f"Mensagem de {mensagem.telefone}: {mensagem.texto}")

    salvar_mensagem(mensagem.telefone, "cliente", mensagem.texto)

    registros = buscar_historico(mensagem.telefone)
    historico_texto = "\n".join([f"{papel}: {msg}" for papel, msg in registros])

    contexto = (
        SYSTEM_PROMPT
        + f"\n\nCliente: {mensagem.nome}"
        + "\n\nHistorico:\n"
        + historico_texto
    )
    
    try:
        resposta = cliente.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=contexto,
            config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        )
    )
        salvar_mensagem(mensagem.telefone, "atendente", resposta.text)
        logger.info(f"Resposta enviada para {mensagem.telefone}")
        return {
            "telefone": mensagem.telefone,
            "resposta": resposta.text
        }

    except Exception as erro:
        logger.error(f"Falha: {erro}")
        return {
            "telefone": mensagem.telefone,
            "resposta": "Estamos com instabilidade. Tente novamente."
        }
@app.post("/whatsapp")
def whatsapp(payload: dict):
    logger.info(f"Webhook recebido: tipo={payload.get('data', {}).get('messageType')}")
    chave_evo = (os.environ.get("EVOLUTION_API_KEY") or "").strip()
    evolution_url = (os.environ.get("EVOLUTION_URL") or "").strip() 
    
    try:
        dados = payload["data"]

        if dados["key"].get("fromMe"):
            return {"status": "ignorado"}

        msg = dados.get("message", {})
        mensagem = msg.get("conversation") or msg.get("extendedTextMessage", {}).get("text")

        if not mensagem:
            logger.info("Mensagem sem texto, ignorada")
            return {"status": "ignorado"}

        telefone = dados["key"]["remoteJid"].split("@")[0]
        nome = dados.get("pushName", "Cliente")

        salvar_mensagem(telefone, "cliente", mensagem)

        registros = buscar_historico(telefone)
        historico_texto = "\n".join([f"{papel}: {msg}" for papel, msg in registros])

        contexto = (
            f"Cliente: {nome}\n\n"
            f"Historico da conversa:\n{historico_texto}\n\n"
            f"MENSAGEM ATUAL do cliente, responda somente a ela:\n{mensagem}"
        )
        resposta = cliente.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=contexto,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT
            )
        )

        salvar_mensagem(telefone, "atendente", resposta.text)

        evolution_url = (os.environ.get("EVOLUTION_URL") or "").strip()
        envio = requests.post(
            f"{evolution_url}/message/sendText/lavi-python",
            headers={"apikey": chave_evo},
            json={"number": telefone, "text": resposta.text},
            timeout=15
        )
        
        logger.info(f"Evolution respondeu {envio.status_code}: {envio.text}")

        return {"status": "ok"}

    except Exception as erro:
        logger.error(f"Erro no webhook: {erro}")

        requests.post(
            f"{evolution_url}/message/sendText/lavi-python",
            headers={"apikey": chave_evo},
            json={"number": telefone, "text": "Estamos com instabilidade no momento. Tente novamente em alguns minutos."},
            timeout=15
        )

        return {"status": "erro"}