import sqlite3

def criar_banco():
    conexao = sqlite3.connect("conversas.db")
    cursor = conexao.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telefone TEXT NOT NULL,
        papel TEXT NOT NULL,
        mensagem TEXT NOT NULL
     )
    """)
    conexao.commit()
    conexao.close()
    print("Banco criado com sucesso.")


def salvar_mensagem(telefone, papel ,mensagem):
    conexao = sqlite3.connect("conversas.db")
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO historico (telefone, papel, mensagem)
        VALUES (?, ?, ?)
    """,      (telefone, papel, mensagem))

    conexao.commit()
    conexao.close()

def buscar_historico(telefone):
    conexao = sqlite3.connect("conversas.db")
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT papel, mensagem FROM historico
        WHERE telefone = ?
        ORDER BY id ASC
    
    """, (telefone,))
    registros = cursor.fetchall()
    conexao.close()
    return registros
    
criar_banco()


