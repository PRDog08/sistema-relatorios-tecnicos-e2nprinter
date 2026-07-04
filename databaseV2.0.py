import psycopg
from psycopg.rows import dict_row
from config import DATABASE_URL


# =========================
# CONEXÃO COM BANCO
# =========================

def get_connection():
    """
    Cria e retorna uma conexão com o PostgreSQL.
    """
    if not DATABASE_URL:
        raise Exception("DATABASE_URL não configurada")

    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


# =========================
# EXECUTOR GENÉRICO
# =========================

def execute_query(query, params=None, fetch=False, fetchone=False):
    """
    Executa queries no banco de forma padronizada.
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(query, params or [])

        result = None

        if fetch:
            result = cur.fetchall()
        elif fetchone:
            result = cur.fetchone()

        conn.commit()
        return result

    except Exception as e:
        conn.rollback()
        print("Erro no banco:", e)
        raise e

    finally:
        cur.close()
        conn.close()


# =========================
# RELATÓRIOS - CRUD
# =========================

def get_relatorios():
    """
    Lista todos os relatórios.
    """
    return execute_query(
        "SELECT * FROM relatorios ORDER BY id DESC",
        fetch=True
    )


def get_relatorio_by_id(relatorio_id):
    """
    Busca um relatório específico.
    """
    return execute_query(
        "SELECT * FROM relatorios WHERE id = %s",
        (relatorio_id,),
        fetchone=True
    )


def create_relatorio(data):
    """
    Cria um novo relatório.
    'data' deve ser um dict com os campos.
    """
    query = """
        INSERT INTO relatorios (
            cliente, telefone, responsavel,
            endereco, cidade, bairro, cep, uf,
            marca, modelo, numero_serie,
            contador_geral,
            motivo, diagnostico, servico_executado,
            hora_inicio, hora_fim
        )
        VALUES (
            %(cliente)s, %(telefone)s, %(responsavel)s,
            %(endereco)s, %(cidade)s, %(bairro)s, %(cep)s, %(uf)s,
            %(marca)s, %(modelo)s, %(numero_serie)s,
            %(contador_geral)s,
            %(motivo)s, %(diagnostico)s, %(servico_executado)s,
            %(hora_inicio)s, %(hora_fim)s
        )
    """

    execute_query(query, data)


def update_relatorio(relatorio_id, data):
    """
    Atualiza um relatório existente.
    """
    query = """
        UPDATE relatorios SET
            cliente = %(cliente)s,
            telefone = %(telefone)s,
            responsavel = %(responsavel)s,
            endereco = %(endereco)s,
            cidade = %(cidade)s,
            bairro = %(bairro)s,
            cep = %(cep)s,
            uf = %(uf)s,
            marca = %(marca)s,
            modelo = %(modelo)s,
            numero_serie = %(numero_serie)s,
            contador_geral = %(contador_geral)s,
            motivo = %(motivo)s,
            diagnostico = %(diagnostico)s,
            servico_executado = %(servico_executado)s,
            hora_inicio = %(hora_inicio)s,
            hora_fim = %(hora_fim)s
        WHERE id = %(id)s
    """

    data["id"] = relatorio_id
    execute_query(query, data)


def delete_relatorio(relatorio_id):
    """
    Remove um relatório.
    """
    execute_query(
        "DELETE FROM relatorios WHERE id = %s",
        (relatorio_id,)
    )