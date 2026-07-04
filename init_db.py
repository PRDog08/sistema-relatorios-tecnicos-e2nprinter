from database import execute_query

# =========================
# CRIAÇÃO DA TABELA PRINCIPAL
# =========================

def criar_tabelas():
    query = """
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
    """

    execute_query(query)
    print("Tabela 'relatorios' verificada/criada com sucesso.")


if __name__ == "__main__":
    criar_tabelas()