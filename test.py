import sqlite3

DB_PATH = "assinaturas.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT * FROM assinaturas")
rows = cursor.fetchall()

# cursor.execute("DELETE FROM assinaturas WHERE chat_id = ?", (5755798350,))
# conn.commit()

# print(f"Removido! Linhas afetadas: {cursor.rowcount}")

# cursor.execute(
#     "UPDATE assinaturas SET data_fim = ? WHERE chat_id = ?",
#     ("2026-02-23", 5755798350)
# )
# conn.commit()

if not rows:
    print("Nenhuma assinatura encontrada.")
else:
    print(f"{'chat_id':<20} {'plano':<10} {'data_inicio':<15} {'data_fim':<15}")
    print("-" * 60)
    for row in rows:
        print(f"{row[0]:<20} {row[1]:<10} {row[2]:<15} {row[3]:<15}")

conn.close()

