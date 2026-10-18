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
Voce e o atendente virtual da Barbearia LaVi.

INFORMACOES:
- Horario: Segunda a sabado das 9h as 19h
- Domingo: FECHADO

SERVICOS E PRECOS:
- Corte: R$ 35
- Barba: R$ 25
- Corte + Barba: R$ 55
- Hidratacao: R$ 40

PAGAMENTO:
- Dinheiro e Pix apenas

REGRAS:
- Nunca invente informacoes
- Respostas curtas e diretas
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
            contents=contexto
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
    logger.info(f"EVOLUTION_URL carregada: {bool(evolution_url)} | tamanho: {len(evolution_url)}")
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
            SYSTEM_PROMPT
            + f"\n\nCliente: {nome}"
            + "\n\nHistorico:\n"
            + historico_texto
        )

        resposta = cliente.models.generate_content(
            model= model="modelo-que-nao-existe",
            contents=contexto
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