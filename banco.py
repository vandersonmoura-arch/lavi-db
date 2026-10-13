import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")


def conectar():
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL não configurada no .env ou no Railway")
    return psycopg2.connect(url)
def criar_banco():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id SERIAL PRIMARY KEY,
            telefone TEXT NOT NULL,
            papel TEXT NOT NULL,
            mensagem TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT NOW()
        )
    """)

    conexao.commit()
    conexao.close()


def salvar_mensagem(telefone, papel, mensagem):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO historico (telefone, papel, mensagem)
        VALUES (%s, %s, %s)
    """, (telefone, papel, mensagem))

    conexao.commit()
    conexao.close()


def buscar_historico(telefone):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT papel, mensagem FROM historico
        WHERE telefone = %s
        ORDER BY id ASC
    """, (telefone,))

    registros = cursor.fetchall()
    conexao.close()
    return registros