import sqlite3
from datetime import datetime

DB_PATH = "relatorios.db"


def gerar_numero_rat(cursor):
    ano_atual = datetime.now().year
    prefixo = f"RAT-{ano_atual}-"

    cursor.execute("""
        SELECT numero_rat
        FROM relatorios
        WHERE numero_rat LIKE ?
        ORDER BY numero_rat DESC
        LIMIT 1
    """, (f"{prefixo}%",))

    ultimo = cursor.fetchone()

    if ultimo and ultimo[0]:
        ultimo_numero = int(ultimo[0].split("-")[-1])
        novo_numero = ultimo_numero + 1
    else:
        novo_numero = 1

    return f"{prefixo}{novo_numero:04d}"


def preencher():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM relatorios
        WHERE numero_rat IS NULL OR numero_rat = ''
        ORDER BY id ASC
    """)

    relatorios_sem_numero = cursor.fetchall()

    if not relatorios_sem_numero:
        print("Todos os relatorios ja possuem numero RAT.")
        conn.close()
        return

    for relatorio in relatorios_sem_numero:
        relatorio_id = relatorio[0]
        numero_rat = gerar_numero_rat(cursor)

        cursor.execute("""
            UPDATE relatorios
            SET numero_rat = ?
            WHERE id = ?
        """, (numero_rat, relatorio_id))

        print(f"Relatorio ID {relatorio_id} recebeu numero {numero_rat}")

    conn.commit()
    conn.close()

    print("Numeracao dos relatorios antigos concluida.")


if __name__ == "__main__":
    preencher()