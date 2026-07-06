from database import execute_query

# =========================
# CRIAÇÃO / ATUALIZAÇÃO DA TABELA
# =========================

def criar_tabelas():

    execute_query("""
        CREATE TABLE IF NOT EXISTS relatorios (

            id SERIAL PRIMARY KEY,

            cliente TEXT,
            telefone TEXT,
            responsavel TEXT,

            endereco TEXT,
            cidade TEXT,
            bairro TEXT,
            cep TEXT,
            uf TEXT,

            marca TEXT,
            modelo TEXT,
            numero_serie TEXT,

            contador_geral TEXT,

            motivo TEXT,
            diagnostico TEXT,
            servico_executado TEXT,

            pecas TEXT,
            status TEXT,
            tecnico TEXT,
            observacoes TEXT,

            hora_inicio TEXT,
            hora_fim TEXT,

            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        );
    """)

    # Compatibilidade com bancos antigos
    colunas = [
        "ALTER TABLE relatorios ADD COLUMN IF NOT EXISTS pecas TEXT;",
        "ALTER TABLE relatorios ADD COLUMN IF NOT EXISTS status TEXT;",
        "ALTER TABLE relatorios ADD COLUMN IF NOT EXISTS tecnico TEXT;",
        "ALTER TABLE relatorios ADD COLUMN IF NOT EXISTS observacoes TEXT;"
    ]

    for coluna in colunas:
        execute_query(coluna)

    print("Banco de dados verificado com sucesso.")


if __name__ == "__main__":
    criar_tabelas()