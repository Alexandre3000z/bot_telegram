import sqlite3
from datetime import datetime, timedelta

DB_PATH = "assinaturas.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assinaturas (
            chat_id INTEGER PRIMARY KEY,
            plano TEXT,
            data_inicio TEXT,
            data_fim TEXT
        )
    """)
    conn.commit()
    conn.close()

DURACAO_PLANOS = {
    "1": 30,
    "2": 60,
    "3": 90,
}

def salvar_assinatura(chat_id: int, plano: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    hoje = datetime.now()
    dias = DURACAO_PLANOS[plano]
    data_fim = hoje + timedelta(days=dias)
    cursor.execute("""
        INSERT INTO assinaturas (chat_id, plano, data_inicio, data_fim)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET
            plano=excluded.plano,
            data_inicio=excluded.data_inicio,
            data_fim=excluded.data_fim
    """, (chat_id, plano, hoje.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

def buscar_expirados():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    hoje = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT chat_id FROM assinaturas WHERE data_fim < ?", (hoje,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def remover_assinatura(chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM assinaturas WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()