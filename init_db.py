from database import execute_query

# =========================
# CRIAÇÃO / ATUALIZAÇÃO DA TABELA
# =========================

def criar_tabelas():
    # Cria a tabela caso não exista
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

        hora_inicio TEXT,
        hora_fim TEXT,

        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Atualiza bancos antigos sem perder dados
    novas_colunas = [
        "ALTER TABLE relatorios ADD COLUMN IF NOT EXISTS pecas TEXT;",
        "ALTER TABLE relatorios ADD COLUMN IF NOT EXISTS status TEXT;",
        "ALTER TABLE relatorios ADD COLUMN IF NOT EXISTS tecnico TEXT;",
        "ALTER TABLE relatorios ADD COLUMN IF NOT EXISTS observacoes TEXT;"
    ]

    for query in novas_colunas:
        execute_query(query)

    print("Tabela 'relatorios' verificada e atualizada com sucesso.")


if __name__ == "__main__":
    criar_tabelas()