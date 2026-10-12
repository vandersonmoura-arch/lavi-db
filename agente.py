from dotenv import load_dotenv
from google import genai
from pathlib import Path
from banco import criar_banco, salvar_mensagem, buscar_historico
import os

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

cliente = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


SYSTEM_PROMPT = """
Você é o atendente virtual da Barbearia LaVi.

INFORMAÇÔES:
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

telefone = input("Qual o seu telefone? ")
nome = input("Qual o seu nome? ")
print(f"\nOlá, {nome}! Bem-vindo à Barbearia LaVi.")

salvar_mensagem(telefone, "sistema", f"Cliente se apresentou: {nome}")

while True:
    pergunta =input(f"\n{nome}, o que deseja saber?")

    if pergunta == "sair":
        print(f"Até logo, {nome}!")
        break

    salvar_mensagem(telefone, "cliente", pergunta)

    registros = buscar_historico(telefone)
    historico_texto = "\n".join([f"{papel}: {msg}" for papel, msg in registros])

    contexto = SYSTEM_PROMPT + "\n\nHistorico da conversa:\n" + historico_texto

    resposta = cliente.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=contexto
    )

    salvar_mensagem(telefone, "atendente", resposta.text)

    print(f"\n{resposta.text}")