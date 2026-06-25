from flask import Flask, render_template, request, redirect, url_for, abort
from dotenv import load_dotenv
from datetime import datetime
import os
import re
import sqlite3

load_dotenv()

app = Flask(__name__)

DATABASE = "relatorios.db"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "123456")
MARCA_PADRAO = "Konica Minolta"

STATUS_PERMITIDOS = {
    "Concluído",
    "Pendente",
    "Aguardando peça",
    "Retorno necessário"
}

MODELOS_KONICA_ATENDIDOS = {
    # Linha Office - A3 Coloridas
    "Bizhub C200",
    "Bizhub C203",
    "Bizhub C220",
    "Bizhub C221",
    "Bizhub C224",
    "Bizhub C224e",
    "Bizhub C227",
    "Bizhub C250",
    "Bizhub C250i",
    "Bizhub C251i",
    "Bizhub C253",
    "Bizhub C258",
    "Bizhub C280",
    "Bizhub C281",
    "Bizhub C284",
    "Bizhub C284e",
    "Bizhub C287",
    "Bizhub C300i",
    "Bizhub C301i",
    "Bizhub C308",
    "Bizhub C353",
    "Bizhub C360",
    "Bizhub C360i",
    "Bizhub C361i",
    "Bizhub C364",
    "Bizhub C364e",
    "Bizhub C368",
    "Bizhub C450i",
    "Bizhub C451i",
    "Bizhub C454",
    "Bizhub C454e",
    "Bizhub C458",
    "Bizhub C550i",
    "Bizhub C551i",
    "Bizhub C554",
    "Bizhub C554e",
    "Bizhub C558",
    "Bizhub C650i",
    "Bizhub C651i",
    "Bizhub C654",
    "Bizhub C654e",
    "Bizhub C658",
    "Bizhub C659",
    "Bizhub C750i",
    "Bizhub C754",
    "Bizhub C754e",
    "Bizhub C759",

    # Linha Office - A4 Coloridas
    "Bizhub C10",
    "Bizhub C20",
    "Bizhub C25",
    "Bizhub C30P",
    "Bizhub C31P",
    "Bizhub C35",
    "Bizhub C35P",
    "Bizhub C3100P",
    "Bizhub C3110",
    "Bizhub C3300i",
    "Bizhub C3320i",
    "Bizhub C3350",
    "Bizhub C3350i",
    "Bizhub C3351",
    "Bizhub C3850",
    "Bizhub C3850FS",
    "Bizhub C3851",
    "Bizhub C3851FS",
    "Bizhub C4000i",
    "Bizhub C4050i",
    "Bizhub C4051i",

    # Linha Pro - Bizhub PRO / Bizhub PRESS
    "Bizhub PRO C500",
    "Bizhub PRO C5500",
    "Bizhub PRO C5501",
    "Bizhub PRO C6000",
    "Bizhub PRO C6000L",
    "Bizhub PRO C6500",
    "Bizhub PRO C6501",
    "Bizhub PRO C7000",
    "Bizhub PRO C7000P",
    "Bizhub PRO C8000",
    "Bizhub PRESS C6000",
    "Bizhub PRESS C7000",
    "Bizhub PRESS C7000P",
    "Bizhub PRESS C70hc",
    "Bizhub PRESS C71hc",
    "Bizhub PRESS C8000",
    "Bizhub PRESS C1060",
    "Bizhub PRESS C1060L",
    "Bizhub PRESS C1070",
    "Bizhub PRESS C1070P",
    "Bizhub PRESS C1085",
    "Bizhub PRESS C1100",

    # Linha Pro - AccurioPrint / AccurioPress
    "AccurioPrint C2060L",
    "AccurioPrint C3070L",
    "AccurioPrint C4065",
    "AccurioPress C2060",
    "AccurioPress C2070",
    "AccurioPress C2070P",
    "AccurioPress C3070",
    "AccurioPress C3070P",
    "AccurioPress C3080",
    "AccurioPress C3080P",
    "AccurioPress C4070",
    "AccurioPress C4080",
    "AccurioPress C5070",
    "AccurioPress C5080",
    "AccurioPress C6085",
    "AccurioPress C6100",
    "AccurioPress C7090",
    "AccurioPress C7100",
    "AccurioPress C10500",
    "AccurioPress C12000",
    "AccurioPress C12010",
    "AccurioPress C14000",
    "AccurioPress C14010",
}


def conectar_banco():
    conexao = sqlite3.connect(DATABASE)
    conexao.row_factory = sqlite3.Row
    return conexao


def limpar_texto(valor):
    return (valor or "").strip()


def somente_numeros(valor):
    return re.sub(r"\D", "", valor or "")


def validar_modelo(equipamento):
    if equipamento not in MODELOS_KONICA_ATENDIDOS:
        abort(400, description="Modelo não permitido. Selecione um equipamento Konica Minolta colorido da linha Office ou Pro.")


def validar_status(status):
    if status not in STATUS_PERMITIDOS:
        abort(400, description="Status inválido.")


def preparar_dados_formulario():
    cliente = limpar_texto(request.form.get("cliente"))
    responsavel = limpar_texto(request.form.get("responsavel"))
    telefone = somente_numeros(request.form.get("telefone"))[:11]
    endereco = limpar_texto(request.form.get("endereco"))
    cidade = limpar_texto(request.form.get("cidade"))
    bairro = limpar_texto(request.form.get("bairro"))
    cep = somente_numeros(request.form.get("cep"))[:8]
    uf = limpar_texto(request.form.get("uf")).upper()[:2]

    marca = MARCA_PADRAO
    equipamento = limpar_texto(request.form.get("equipamento"))
    numero_serie = limpar_texto(request.form.get("numero_serie"))
    contador_geral = limpar_texto(request.form.get("contador_geral"))

    hora_inicio = limpar_texto(request.form.get("hora_inicio"))
    hora_fim = limpar_texto(request.form.get("hora_fim"))

    defeito_relatado = limpar_texto(request.form.get("defeito_relatado"))
    diagnostico = limpar_texto(request.form.get("diagnostico"))
    servico_executado = limpar_texto(request.form.get("servico_executado"))
    pecas = limpar_texto(request.form.get("pecas"))
    status = limpar_texto(request.form.get("status"))
    observacoes = limpar_texto(request.form.get("observacoes"))
    tecnico = limpar_texto(request.form.get("tecnico"))

    if not cliente:
        abort(400, description="O campo Cliente é obrigatório.")

    if not equipamento:
        abort(400, description="O campo Equipamento / Modelo é obrigatório.")

    validar_modelo(equipamento)

    if not defeito_relatado:
        abort(400, description="O campo Defeito relatado é obrigatório.")

    if not diagnostico:
        abort(400, description="O campo Diagnóstico técnico é obrigatório.")

    if not servico_executado:
        abort(400, description="O campo Serviço executado é obrigatório.")

    if not status:
        abort(400, description="O campo Status é obrigatório.")

    validar_status(status)

    if not tecnico:
        abort(400, description="O campo Técnico é obrigatório.")

    return {
        "cliente": cliente,
        "responsavel": responsavel,
        "telefone": telefone,
        "endereco": endereco,
        "cidade": cidade,
        "bairro": bairro,
        "cep": cep,
        "uf": uf,
        "marca": marca,
        "equipamento": equipamento,
        "numero_serie": numero_serie,
        "contador_geral": contador_geral,
        "hora_inicio": hora_inicio,
        "hora_fim": hora_fim,
        "defeito_relatado": defeito_relatado,
        "diagnostico": diagnostico,
        "servico_executado": servico_executado,
        "pecas": pecas,
        "status": status,
        "observacoes": observacoes,
        "tecnico": tecnico,
    }


def criar_tabela():
    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relatorios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            telefone TEXT,
            endereco TEXT,
            equipamento TEXT NOT NULL,
            numero_serie TEXT,
            contador_pb TEXT,
            contador_color TEXT,
            defeito_relatado TEXT NOT NULL,
            diagnostico TEXT NOT NULL,
            servico_executado TEXT NOT NULL,
            pecas TEXT,
            status TEXT NOT NULL,
            observacoes TEXT,
            tecnico TEXT NOT NULL,
            criado_em TEXT NOT NULL
        )
    """)

    cursor.execute("PRAGMA table_info(relatorios)")
    colunas_existentes = [coluna["name"] for coluna in cursor.fetchall()]

    novas_colunas = {
        "responsavel": "TEXT",
        "cidade": "TEXT",
        "bairro": "TEXT",
        "cep": "TEXT",
        "uf": "TEXT",
        "hora_inicio": "TEXT",
        "hora_fim": "TEXT",
        "marca": "TEXT",
        "contador_geral": "TEXT"
    }

    for nome_coluna, tipo_coluna in novas_colunas.items():
        if nome_coluna not in colunas_existentes:
            cursor.execute(
                f"ALTER TABLE relatorios ADD COLUMN {nome_coluna} {tipo_coluna}"
            )

    conexao.commit()
    conexao.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/criar-relatorio", methods=["POST"])
def criar_relatorio():
    dados = preparar_dados_formulario()
    criado_em = datetime.now().strftime("%d/%m/%Y %H:%M")

    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO relatorios (
            cliente,
            responsavel,
            telefone,
            endereco,
            cidade,
            bairro,
            cep,
            uf,
            marca,
            equipamento,
            numero_serie,
            contador_geral,
            hora_inicio,
            hora_fim,
            defeito_relatado,
            diagnostico,
            servico_executado,
            pecas,
            status,
            observacoes,
            tecnico,
            criado_em
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        dados["cliente"],
        dados["responsavel"],
        dados["telefone"],
        dados["endereco"],
        dados["cidade"],
        dados["bairro"],
        dados["cep"],
        dados["uf"],
        dados["marca"],
        dados["equipamento"],
        dados["numero_serie"],
        dados["contador_geral"],
        dados["hora_inicio"],
        dados["hora_fim"],
        dados["defeito_relatado"],
        dados["diagnostico"],
        dados["servico_executado"],
        dados["pecas"],
        dados["status"],
        dados["observacoes"],
        dados["tecnico"],
        criado_em
    ))

    conexao.commit()
    relatorio_id = cursor.lastrowid
    conexao.close()

    return redirect(url_for("ver_relatorio", relatorio_id=relatorio_id, token=ADMIN_TOKEN))


@app.route("/admin")
def admin():
    token = request.args.get("token")

    if token != ADMIN_TOKEN:
        abort(403)

    busca = request.args.get("busca", "")

    conexao = conectar_banco()
    cursor = conexao.cursor()

    if busca:
        cursor.execute("""
            SELECT * FROM relatorios
            WHERE cliente LIKE ?
               OR equipamento LIKE ?
               OR tecnico LIKE ?
               OR responsavel LIKE ?
            ORDER BY id DESC
        """, (
            f"%{busca}%",
            f"%{busca}%",
            f"%{busca}%",
            f"%{busca}%"
        ))
    else:
        cursor.execute("""
            SELECT * FROM relatorios
            ORDER BY id DESC
        """)

    relatorios = cursor.fetchall()
    conexao.close()

    total = len(relatorios)
    concluidos = sum(1 for r in relatorios if r["status"] == "Concluído")
    pendentes = sum(1 for r in relatorios if r["status"] == "Pendente")
    aguardando_peca = sum(1 for r in relatorios if r["status"] == "Aguardando peça")
    retorno = sum(1 for r in relatorios if r["status"] == "Retorno necessário")

    return render_template(
        "admin.html",
        relatorios=relatorios,
        busca=busca,
        token=token,
        total=total,
        concluidos=concluidos,
        pendentes=pendentes,
        aguardando_peca=aguardando_peca,
        retorno=retorno
    )


@app.route("/relatorio/<int:relatorio_id>")
def ver_relatorio(relatorio_id):
    token = request.args.get("token")

    if token != ADMIN_TOKEN:
        abort(403)

    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("SELECT * FROM relatorios WHERE id = ?", (relatorio_id,))
    relatorio = cursor.fetchone()

    conexao.close()

    if relatorio is None:
        abort(404)

    return render_template("relatorio.html", relatorio=relatorio, token=token)


@app.route("/relatorio/<int:relatorio_id>/editar", methods=["GET", "POST"])
def editar_relatorio(relatorio_id):
    token = request.args.get("token")

    if token != ADMIN_TOKEN:
        abort(403)

    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("SELECT * FROM relatorios WHERE id = ?", (relatorio_id,))
    relatorio = cursor.fetchone()

    if relatorio is None:
        conexao.close()
        abort(404)

    if request.method == "POST":
        dados = preparar_dados_formulario()

        cursor.execute("""
            UPDATE relatorios
            SET
                cliente = ?,
                responsavel = ?,
                telefone = ?,
                endereco = ?,
                cidade = ?,
                bairro = ?,
                cep = ?,
                uf = ?,
                marca = ?,
                equipamento = ?,
                numero_serie = ?,
                contador_geral = ?,
                hora_inicio = ?,
                hora_fim = ?,
                defeito_relatado = ?,
                diagnostico = ?,
                servico_executado = ?,
                pecas = ?,
                status = ?,
                observacoes = ?,
                tecnico = ?
            WHERE id = ?
        """, (
            dados["cliente"],
            dados["responsavel"],
            dados["telefone"],
            dados["endereco"],
            dados["cidade"],
            dados["bairro"],
            dados["cep"],
            dados["uf"],
            dados["marca"],
            dados["equipamento"],
            dados["numero_serie"],
            dados["contador_geral"],
            dados["hora_inicio"],
            dados["hora_fim"],
            dados["defeito_relatado"],
            dados["diagnostico"],
            dados["servico_executado"],
            dados["pecas"],
            dados["status"],
            dados["observacoes"],
            dados["tecnico"],
            relatorio_id
        ))

        conexao.commit()
        conexao.close()

        return redirect(url_for("ver_relatorio", relatorio_id=relatorio_id, token=token))

    conexao.close()

    return render_template("editar.html", relatorio=relatorio, token=token)


@app.route("/relatorio/<int:relatorio_id>/excluir", methods=["POST"])
def excluir_relatorio(relatorio_id):
    token = request.args.get("token")

    if token != ADMIN_TOKEN:
        abort(403)

    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("DELETE FROM relatorios WHERE id = ?", (relatorio_id,))

    conexao.commit()
    conexao.close()

    return redirect(url_for("admin", token=token))


criar_tabela()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)