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
Você é o atendente virtual da Barbearia LaVi.

INFORMAÇÕES:
- Horário: Segunda a sábado das 9h às 19h
- Domingo: FECHADO

SERVIÇOS E PREÇOS:
- Corte: R$ 35
- Barba: R$ 25
- Corte + Barba: R$ 55
- Hidratação: R$ 40

PAGAMENTO:
- Dinheiro e Pix apenas

REGRAS:
- Nunca invente informações
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
    try:
        mensagem = payload["data"]["message"]["conversation"]
        telefone = payload["data"]["key"]["remoteJid"].replace("@s.whatsapp.net", "")
        nome = payload["data"]["pushName"]

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
            model="gemini-3.5-flash-lite",
            contents=contexto
        )

        salvar_mensagem(telefone, "atendente", resposta.text)
        logger.info(f"WhatsApp respondido para {telefone}")

        return {"status": "ok"}

    except Exception as erro:
        logger.error(f"Erro no webhook: {erro}")
        return {"status": "erro"}