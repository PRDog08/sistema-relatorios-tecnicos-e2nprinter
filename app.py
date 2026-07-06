import os
import re
from datetime import datetime

from flask import Flask, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "troque-esta-chave-em-producao")

database_url = os.getenv("DATABASE_URL", "sqlite:///relatorios.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
app.db_initialized = False


class Relatorio(db.Model):
    __tablename__ = "relatorios"

    id = db.Column(db.Integer, primary_key=True)
    cliente = db.Column(db.String(200), nullable=False)
    responsavel = db.Column(db.String(200))
    telefone = db.Column(db.String(20), nullable=False)

    endereco = db.Column(db.String(200))
    cep = db.Column(db.String(10))
    cidade = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    uf = db.Column(db.String(5))

    marca = db.Column(db.String(100), default="Konica Minolta")
    equipamento = db.Column("modelo", db.String(150), nullable=False)
    numero_serie = db.Column(db.String(100))
    contador_geral = db.Column(db.String(100))

    hora_inicio = db.Column(db.String(10))
    hora_fim = db.Column(db.String(10))

    defeito_relatado = db.Column("motivo", db.Text)
    diagnostico = db.Column(db.Text)
    servico_executado = db.Column(db.Text)
    pecas = db.Column(db.Text)

    status = db.Column(db.String(50), default="Concluido")
    tecnico = db.Column(db.String(100))
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def modelo(self):
        return self.equipamento

    @property
    def motivo(self):
        return self.defeito_relatado

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __getitem__(self, key):
        return getattr(self, key)


def clean(texto):
    return (texto or "").strip().replace("<", "").replace(">", "")


def admin_autorizado():
    token_configurado = os.getenv("ADMIN_TOKEN")
    token_informado = request.args.get("token") or request.form.get("token")

    if not token_configurado:
        return True

    if session.get("admin_ok"):
        return True

    if token_informado == token_configurado:
        session["admin_ok"] = True
        return True

    return False


def exigir_login():
    if not admin_autorizado():
        return redirect(url_for("login"))
    return None


def contar_status(*status_possiveis):
    return Relatorio.query.filter(Relatorio.status.in_(status_possiveis)).count()


def validar_relatorio(form):
    cliente = clean(form.get("cliente"))
    telefone = clean(form.get("telefone"))
    equipamento = clean(form.get("equipamento") or form.get("modelo"))
    cep = clean(form.get("cep"))

    if not cliente:
        return "Cliente obrigatorio"

    if not telefone or not re.fullmatch(r"\d{10,11}", telefone):
        return "Telefone invalido. Informe apenas numeros com DDD."

    if cep and not re.fullmatch(r"\d{8}", cep):
        return "CEP invalido. Informe apenas 8 numeros."

    if not equipamento:
        return "Equipamento/modelo obrigatorio"

    return None


@app.context_processor
def variaveis_globais():
    return {
        "system_name": "E2nPrinter - Relatorios Tecnicos",
        "token": request.args.get("token", ""),
    }


@app.before_request
def inicializar_banco():
    if not app.db_initialized:
        db.create_all()
        app.db_initialized = True


@app.route("/")
def index():
    return redirect(url_for("admin"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if admin_autorizado():
            return redirect(url_for("admin"))
        return "Token invalido", 401

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/admin")
def admin():
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio

    busca = clean(request.args.get("busca"))
    query = Relatorio.query

    if busca:
        termo = f"%{busca}%"
        query = query.filter(
            or_(
                Relatorio.cliente.ilike(termo),
                Relatorio.responsavel.ilike(termo),
                Relatorio.equipamento.ilike(termo),
                Relatorio.tecnico.ilike(termo),
            )
        )

    relatorios = query.order_by(Relatorio.id.desc()).all()

    return render_template(
        "admin.html",
        relatorios=relatorios,
        total=Relatorio.query.count(),
        concluidos=contar_status("Concluido", "Concluído"),
        pendentes=contar_status("Pendente"),
        aguardando_peca=contar_status("Aguardando peca", "Aguardando peça"),
        retorno=contar_status("Retorno necessario", "Retorno necessário"),
        busca=busca,
    )


@app.route("/novo")
@app.route("/relatorio/novo")
@app.route("/novo_relatorio")
def novo_relatorio():
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio

    return render_template("novo.html")


@app.route("/criar_relatorio", methods=["POST"])
def criar_relatorio():
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio

    erro = validar_relatorio(request.form)
    if erro:
        return erro, 400

    relatorio = Relatorio(
        cliente=clean(request.form.get("cliente")),
        responsavel=clean(request.form.get("responsavel")),
        telefone=clean(request.form.get("telefone")),
        endereco=clean(request.form.get("endereco")),
        cep=clean(request.form.get("cep")),
        cidade=clean(request.form.get("cidade")),
        bairro=clean(request.form.get("bairro")),
        uf=clean(request.form.get("uf")).upper(),
        marca=clean(request.form.get("marca")) or "Konica Minolta",
        equipamento=clean(request.form.get("equipamento") or request.form.get("modelo")),
        numero_serie=clean(request.form.get("numero_serie") or request.form.get("serie")),
        contador_geral=clean(request.form.get("contador_geral")),
        hora_inicio=clean(request.form.get("hora_inicio")),
        hora_fim=clean(request.form.get("hora_fim")),
        defeito_relatado=clean(request.form.get("defeito_relatado") or request.form.get("descricao")),
        diagnostico=clean(request.form.get("diagnostico") or request.form.get("solucao")),
        servico_executado=clean(request.form.get("servico_executado")),
        pecas=clean(request.form.get("pecas")),
        status=clean(request.form.get("status")) or "Concluido",
        tecnico=clean(request.form.get("tecnico")),
        observacoes=clean(request.form.get("observacoes")),
    )

    db.session.add(relatorio)
    db.session.commit()

    return redirect(url_for("admin"))


@app.route("/editar_relatorio/<int:relatorio_id>", methods=["GET", "POST"])
@app.route("/editar/<int:relatorio_id>", methods=["GET", "POST"])
@app.route("/relatorio/editar/<int:relatorio_id>", methods=["GET", "POST"])
def editar_relatorio(relatorio_id):
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio

    relatorio = Relatorio.query.get_or_404(relatorio_id)

    if request.method == "POST":
        erro = validar_relatorio(request.form)
        if erro:
            return erro, 400

        relatorio.cliente = clean(request.form.get("cliente"))
        relatorio.responsavel = clean(request.form.get("responsavel"))
        relatorio.telefone = clean(request.form.get("telefone"))
        relatorio.endereco = clean(request.form.get("endereco"))
        relatorio.cep = clean(request.form.get("cep"))
        relatorio.cidade = clean(request.form.get("cidade"))
        relatorio.bairro = clean(request.form.get("bairro"))
        relatorio.uf = clean(request.form.get("uf")).upper()
        relatorio.marca = clean(request.form.get("marca")) or "Konica Minolta"
        relatorio.equipamento = clean(request.form.get("equipamento") or request.form.get("modelo"))
        relatorio.numero_serie = clean(request.form.get("numero_serie") or request.form.get("serie"))
        relatorio.contador_geral = clean(request.form.get("contador_geral"))
        relatorio.hora_inicio = clean(request.form.get("hora_inicio"))
        relatorio.hora_fim = clean(request.form.get("hora_fim"))
        relatorio.defeito_relatado = clean(request.form.get("defeito_relatado") or request.form.get("descricao"))
        relatorio.diagnostico = clean(request.form.get("diagnostico") or request.form.get("solucao"))
        relatorio.servico_executado = clean(request.form.get("servico_executado"))
        relatorio.pecas = clean(request.form.get("pecas"))
        relatorio.status = clean(request.form.get("status")) or "Concluido"
        relatorio.tecnico = clean(request.form.get("tecnico"))
        relatorio.observacoes = clean(request.form.get("observacoes"))

        db.session.commit()
        return redirect(url_for("admin"))

    return render_template("editar.html", relatorio=relatorio)


@app.route("/relatorio/<int:relatorio_id>")
@app.route("/ver_relatorio/<int:relatorio_id>")
def ver_relatorio(relatorio_id):
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio

    relatorio = Relatorio.query.get_or_404(relatorio_id)
    return render_template("relatorio.html", relatorio=relatorio)


@app.route("/excluir/<int:relatorio_id>", methods=["POST"])
@app.route("/excluir_relatorio/<int:relatorio_id>", methods=["POST"])
def excluir_relatorio(relatorio_id):
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio

    relatorio = Relatorio.query.get_or_404(relatorio_id)
    db.session.delete(relatorio)
    db.session.commit()
    return redirect(url_for("admin"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=os.getenv("DEBUG", "False").lower() == "true")
