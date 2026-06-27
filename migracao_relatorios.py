import sqlite3
from pathlib import Path

DB_PATH = Path("relatorios.db")


def coluna_existe(cursor, tabela, coluna):
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas = [linha[1] for linha in cursor.fetchall()]
    return coluna in colunas


def tabela_existe(cursor, tabela):
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (tabela,)
    )
    return cursor.fetchone() is not None


def migrar():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if not tabela_existe(cursor, "clientes"):
        cursor.execute("""
            CREATE TABLE clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                telefone TEXT,
                email TEXT,
                endereco TEXT,
                documento TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Tabela clientes criada.")
    else:
        print("Tabela clientes ja existe.")

    if tabela_existe(cursor, "relatorios"):
        novas_colunas = {
            "numero_rat": "TEXT",
            "cliente_id": "INTEGER",
            "assinatura_cliente": "TEXT",
            "assinatura_nome": "TEXT",
            "assinatura_data": "TIMESTAMP"
        }

        for coluna, tipo in novas_colunas.items():
            if not coluna_existe(cursor, "relatorios", coluna):
                cursor.execute(f"ALTER TABLE relatorios ADD COLUMN {coluna} {tipo}")
                print(f"Coluna {coluna} adicionada em relatorios.")
            else:
                print(f"Coluna {coluna} ja existe em relatorios.")
    else:
        print("ATENCAO: tabela relatorios nao encontrada.")

    if not tabela_existe(cursor, "pecas_relatorio"):
        cursor.execute("""
            CREATE TABLE pecas_relatorio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                relatorio_id INTEGER NOT NULL,
                nome_peca TEXT NOT NULL,
                quantidade INTEGER DEFAULT 1,
                valor_unitario REAL DEFAULT 0,
                observacao TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (relatorio_id) REFERENCES relatorios(id)
            )
        """)
        print("Tabela pecas_relatorio criada.")
    else:
        print("Tabela pecas_relatorio ja existe.")

    if tabela_existe(cursor, "relatorios"):
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_relatorios_numero_rat
            ON relatorios(numero_rat)
            WHERE numero_rat IS NOT NULL
        """)
        print("Indice unico para numero_rat criado/verificado.")

    conn.commit()
    conn.close()

    print("Migracao concluida com sucesso.")


if __name__ == "__main__":
    migrar()