from flask import Flask, render_template, request, redirect, url_for, session
from config import ADMIN_TOKEN
from database import (
    get_relatorios,
    get_relatorio_by_id,
    create_relatorio,
    update_relatorio,
    delete_relatorio
)
from init_db import criar_tabelas

app = Flask(__name__)
app.secret_key = "e2nprinter_secret_key"


# =========================
# INIT DB (SEGURO PARA RENDER)
# =========================
@app.before_request
def init_db_once():
    if not hasattr(app, "db_initialized"):
        criar_tabelas()
        app.db_initialized = True


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        token = request.form.get("token")

        if token == ADMIN_TOKEN:
            session["auth"] = True
            return redirect(url_for("index"))

        return render_template(
            "login.html",
            erro="Token de acesso inválido."
), 401

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def auth_required():
    return session.get("auth") is True


# =========================
# HOME
# =========================
@app.route("/")
def index():
    if not auth_required():
        return redirect(url_for("login"))

    relatorios = get_relatorios()
    return render_template("index.html", relatorios=relatorios)


# =========================
# NOVO RELATÓRIO
# =========================
@app.route("/relatorio/novo", methods=["GET", "POST"])
def novo_relatorio():
    if not auth_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        data = {
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "responsavel": request.form.get("responsavel"),
            "endereco": request.form.get("endereco"),
            "cidade": request.form.get("cidade"),
            "bairro": request.form.get("bairro"),
            "cep": request.form.get("cep"),
            "uf": request.form.get("uf"),
            "marca": request.form.get("marca"),
            "modelo": request.form.get("equipamento"),  # FIX REAL
            "numero_serie": request.form.get("numero_serie"),
            "contador_geral": request.form.get("contador_geral"),
            "motivo": request.form.get("defeito_relatado"),
            "diagnostico": request.form.get("diagnostico"),
            "servico_executado": request.form.get("servico_executado"),
            "pecas": request.form.get("pecas"),
            "hora_inicio": request.form.get("hora_inicio"),
            "hora_fim": request.form.get("hora_fim"),
            "status": request.form.get("status"),
            "tecnico": request.form.get("tecnico"),
            "observacoes": request.form.get("observacoes")
        }

        create_relatorio(data)
        return redirect(url_for("index"))

    return render_template("novo.html")


# =========================
# EDITAR
# =========================
@app.route("/relatorio/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if not auth_required():
        return redirect(url_for("login"))

    relatorio = get_relatorio_by_id(id)

    if request.method == "POST":
        data = {
            "cliente": request.form.get("cliente"),
            "telefone": request.form.get("telefone"),
            "responsavel": request.form.get("responsavel"),
            "endereco": request.form.get("endereco"),
            "cidade": request.form.get("cidade"),
            "bairro": request.form.get("bairro"),
            "cep": request.form.get("cep"),
            "uf": request.form.get("uf"),
            "marca": request.form.get("marca"),
            "modelo": request.form.get("equipamento"),
            "numero_serie": request.form.get("numero_serie"),
            "contador_geral": request.form.get("contador_geral"),
            "motivo": request.form.get("defeito_relatado"),
            "diagnostico": request.form.get("diagnostico"),
            "servico_executado": request.form.get("servico_executado"),
            "pecas": request.form.get("pecas"),
            "hora_inicio": request.form.get("hora_inicio"),
            "hora_fim": request.form.get("hora_fim"),
            "status": request.form.get("status"),
            "tecnico": request.form.get("tecnico"),
            "observacoes": request.form.get("observacoes")
        }

        update_relatorio(id, data)
        return redirect(url_for("index"))

    return render_template("editar.html", relatorio=relatorio)


# =========================
# DELETE
# =========================
@app.route("/relatorio/deletar/<int:id>")
def deletar(id):
    if not auth_required():
        return redirect(url_for("login"))

    delete_relatorio(id)
    return redirect(url_for("index"))


# =========================
# VIEW
# =========================
@app.route("/relatorio/<int:id>")
def ver_relatorio(id):
    if not auth_required():
        return redirect(url_for("login"))

    relatorio = get_relatorio_by_id(id)
    return render_template("relatorio.html", relatorio=relatorio)


# =========================
# START
# =========================
if __name__ == "__main__":
    app.run()