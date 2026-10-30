import base64
import binascii
import json
import os
import re
import secrets
from datetime import datetime
from urllib.parse import urlencode
from urllib.error import URLError
from urllib.request import urlopen

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, inspect, or_, text


app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "troque-esta-chave-em-producao")

database_url = os.getenv("DATABASE_URL", "sqlite:///relatorios.db")

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
elif database_url.startswith("postgresql+psycopg://"):
    database_url = database_url.replace("postgresql+psycopg://", "postgresql+psycopg2://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

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
    assinatura_cliente = db.Column(db.Text)
    token_compartilhamento = db.Column(
        db.String(64), default=lambda: secrets.token_urlsafe(32), index=True
    )
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


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    empresa = db.Column(db.String(200), nullable=False, index=True)
    responsavel = db.Column(db.String(200))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(150))
    endereco = db.Column(db.String(200))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    cep = db.Column(db.String(10))
    uf = db.Column(db.String(2))
    cnpj = db.Column(db.String(18), index=True)
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def para_json(self):
        return {
            "id": self.id,
            "empresa": self.empresa,
            "responsavel": self.responsavel,
            "telefone": self.telefone,
            "email": self.email,
            "endereco": self.endereco,
            "bairro": self.bairro,
            "cidade": self.cidade,
            "cep": self.cep,
            "uf": self.uf,
            "cnpj": self.cnpj,
            "observacoes": self.observacoes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def clean(texto):
    return (texto or "").strip().replace("<", "").replace(">", "")


def apenas_numeros(texto):
    return re.sub(r"\D", "", texto or "")


def assinatura_do_formulario(form):
    valor = (form.get("assinatura_cliente") or "").strip()
    if not valor:
        return None, None

    prefixo = "data:image/png;base64,"
    if not valor.startswith(prefixo) or len(valor) > 1_400_000:
        return None, "Assinatura invalida ou muito grande. Limpe o campo e tente novamente."

    try:
        imagem = base64.b64decode(valor[len(prefixo):], validate=True)
    except (binascii.Error, ValueError):
        return None, "Nao foi possivel ler a imagem da assinatura."

    if len(imagem) > 1_000_000 or not imagem.startswith(b"\x89PNG\r\n\x1a\n"):
        return None, "A assinatura precisa ser uma imagem PNG valida de ate 1 MB."

    return valor, None


def novo_token_compartilhamento():
    return secrets.token_urlsafe(32)


def formatar_cep(texto):
    cep = apenas_numeros(texto)[:8]
    if len(cep) == 8:
        return f"{cep[:5]}-{cep[5:]}"
    return cep


def dados_cliente(form):
    return {
        "empresa": clean(form.get("empresa")),
        "responsavel": clean(form.get("responsavel")),
        "telefone": apenas_numeros(form.get("telefone")),
        "email": clean(form.get("email")),
        "endereco": clean(form.get("endereco")),
        "bairro": clean(form.get("bairro")),
        "cidade": clean(form.get("cidade")),
        "cep": formatar_cep(form.get("cep")),
        "uf": clean(form.get("uf")).upper(),
        "cnpj": apenas_numeros(form.get("cnpj")),
        "observacoes": clean(form.get("observacoes")),
    }


def validar_cliente(dados):
    if not dados["empresa"]:
        return "Empresa obrigatoria"

    if dados["telefone"] and not re.fullmatch(r"\d{10,11}", dados["telefone"]):
        return "Telefone invalido. Informe 10 ou 11 numeros com DDD."

    if dados["cep"] and not re.fullmatch(r"\d{8}", apenas_numeros(dados["cep"])):
        return "CEP invalido. Informe 8 numeros."

    if dados["uf"] and not re.fullmatch(r"[A-Z]{2}", dados["uf"]):
        return "UF invalida. Informe a sigla com duas letras."

    if dados["cnpj"] and not re.fullmatch(r"\d{14}", dados["cnpj"]):
        return "CNPJ invalido. Informe 14 numeros."

    return None


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
    cep = apenas_numeros(form.get("cep"))

    if not cliente:
        return "Cliente obrigatorio"

    if not telefone or not re.fullmatch(r"\d{10,11}", telefone):
        return "Telefone invalido. Informe apenas numeros com DDD."

    if cep and not re.fullmatch(r"\d{8}", cep):
        return "CEP invalido. Informe apenas 8 numeros."

    if not equipamento:
        return "Equipamento/modelo obrigatorio"

    return None


PECAS_SCHEMA = "e2nprinter-pecas-v1"


def ler_pecas(valor):
    """Retorna as peças estruturadas e preserva os textos antigos como legado."""
    if not valor:
        return {"itens": [], "legado": ""}

    try:
        dados = json.loads(valor)
    except (TypeError, ValueError):
        dados = None

    if isinstance(dados, dict) and dados.get("schema") == PECAS_SCHEMA:
        itens = dados.get("itens") or []
        return {
            "itens": [
                {
                    "status": clean(item.get("status")) if isinstance(item, dict) else "",
                    "quantidade": clean(item.get("quantidade")) if isinstance(item, dict) else "",
                    "descricao": clean(item.get("descricao")) if isinstance(item, dict) else "",
                    "codigo": clean(item.get("codigo")) if isinstance(item, dict) else "",
                }
                for item in itens
                if isinstance(item, dict)
            ],
            "legado": "",
        }

    texto = clean(valor)
    if texto.casefold().rstrip(".") in {"nenhuma peca informada", "nenhuma peça informada"}:
        return {"itens": [], "legado": ""}
    return {"itens": [], "legado": texto}


def salvar_pecas(form):
    nomes = ("peca_status", "peca_quantidade", "peca_descricao", "peca_codigo")
    listas = [form.getlist(nome) for nome in nomes]
    quantidade_linhas = min(max((len(lista) for lista in listas), default=0), 8)
    itens = []

    for indice in range(quantidade_linhas):
        valores = [clean(lista[indice]) if indice < len(lista) else "" for lista in listas]
        item = {
            "status": valores[0] if valores[0] in {"A", "T", "E"} else "",
            "quantidade": valores[1],
            "descricao": valores[2],
            "codigo": valores[3],
        }
        if any(item.values()):
            itens.append(item)

    if not itens:
        return ""
    return json.dumps({"schema": PECAS_SCHEMA, "itens": itens}, ensure_ascii=False)


def codigos_pecas_utilizados():
    codigos = set()
    for (valor,) in db.session.query(Relatorio.pecas).filter(Relatorio.pecas.isnot(None)).all():
        for item in ler_pecas(valor)["itens"]:
            codigo = item["codigo"].strip()
            if codigo:
                codigos.add(codigo)
    return sorted(codigos, key=str.casefold)


def buscar_contador_anterior(numero_serie, antes_id=None):
    serie = clean(numero_serie)
    if not serie:
        return ""

    consulta = Relatorio.query.filter(
        func.lower(func.trim(Relatorio.numero_serie)) == serie.casefold(),
        Relatorio.contador_geral.isnot(None),
        func.trim(Relatorio.contador_geral) != "",
    )
    if antes_id is not None:
        consulta = consulta.filter(Relatorio.id < antes_id)
    anterior = consulta.order_by(Relatorio.id.desc()).first()
    return anterior.contador_geral if anterior else ""


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
        colunas = {coluna["name"] for coluna in inspect(db.engine).get_columns("relatorios")}
        with db.engine.begin() as conexao:
            if "assinatura_cliente" not in colunas:
                conexao.execute(text("ALTER TABLE relatorios ADD COLUMN assinatura_cliente TEXT"))
            if "token_compartilhamento" not in colunas:
                conexao.execute(text("ALTER TABLE relatorios ADD COLUMN token_compartilhamento VARCHAR(64)"))
            conexao.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_relatorios_token_compartilhamento "
                "ON relatorios (token_compartilhamento)"
            ))

        relatorios_sem_token = Relatorio.query.filter(
            or_(Relatorio.token_compartilhamento.is_(None), Relatorio.token_compartilhamento == "")
        ).all()
        for relatorio in relatorios_sem_token:
            relatorio.token_compartilhamento = novo_token_compartilhamento()
        if relatorios_sem_token:
            db.session.commit()
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


@app.route("/clientes")
def listar_clientes():
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio

    busca = clean(request.args.get("busca"))
    query = Cliente.query

    if busca:
        termo = f"%{busca}%"
        query = query.filter(
            or_(
                Cliente.empresa.ilike(termo),
                Cliente.responsavel.ilike(termo),
                Cliente.telefone.ilike(termo),
                Cliente.email.ilike(termo),
                Cliente.cnpj.ilike(termo),
                Cliente.cidade.ilike(termo),
            )
        )

    clientes = query.order_by(Cliente.empresa.asc(), Cliente.id.desc()).all()
    return render_template("clientes.html", clientes=clientes, busca=busca)


@app.route("/clientes/novo", methods=["GET", "POST"])
def criar_cliente():
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio

    if request.method == "POST":
        dados = dados_cliente(request.form)
        erro = validar_cliente(dados)
        if erro:
            return erro, 400

        cliente = Cliente(**dados)
        db.session.add(cliente)
        db.session.commit()
        return redirect(url_for("listar_clientes"))

    return render_template("cliente_form.html", cliente=None)


@app.route("/clientes/<int:cliente_id>/editar", methods=["GET", "POST"])
def editar_cliente(cliente_id):
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio

    cliente = Cliente.query.get_or_404(cliente_id)

    if request.method == "POST":
        dados = dados_cliente(request.form)
        erro = validar_cliente(dados)
        if erro:
            return erro, 400

        for campo, valor in dados.items():
            setattr(cliente, campo, valor)

        db.session.commit()
        return redirect(url_for("listar_clientes"))

    return render_template("cliente_form.html", cliente=cliente)


@app.route("/clientes/<int:cliente_id>/excluir", methods=["POST"])
def excluir_cliente(cliente_id):
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio

    cliente = Cliente.query.get_or_404(cliente_id)
    db.session.delete(cliente)
    db.session.commit()
    return redirect(url_for("listar_clientes"))


@app.route("/api/clientes")
def api_clientes():
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio

    busca = clean(request.args.get("q"))
    if len(busca) < 2:
        return jsonify([])

    termo = f"%{busca}%"
    clientes = (
        Cliente.query.filter(
            or_(
                Cliente.empresa.ilike(termo),
                Cliente.responsavel.ilike(termo),
                Cliente.cnpj.ilike(termo),
            )
        )
        .order_by(Cliente.empresa.asc())
        .limit(8)
        .all()
    )
    return jsonify(
        [
            {
                "id": cliente.id,
                "empresa": cliente.empresa,
                "responsavel": cliente.responsavel,
                "cidade": cliente.cidade,
                "cnpj": cliente.cnpj,
            }
            for cliente in clientes
        ]
    )


@app.route("/api/clientes/<int:cliente_id>")
def api_cliente(cliente_id):
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio

    cliente = Cliente.query.get_or_404(cliente_id)
    return jsonify(cliente.para_json())


@app.route("/api/cep/<cep>")
def api_cep(cep):
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio

    cep = apenas_numeros(cep)
    if not re.fullmatch(r"\d{8}", cep):
        return jsonify({"erro": True, "mensagem": "CEP invalido."}), 400

    try:
        with urlopen(f"https://viacep.com.br/ws/{cep}/json/", timeout=5) as resposta:
            dados = json.load(resposta)
    except (URLError, ValueError, OSError):
        return jsonify({"erro": True, "mensagem": "Nao foi possivel consultar o CEP."}), 502

    return jsonify(dados)


@app.route("/api/contador-anterior")
def api_contador_anterior():
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio

    numero_serie = request.args.get("numero_serie", "")
    relatorio_id = request.args.get("relatorio_id", type=int)
    return jsonify({
        "contador_anterior": buscar_contador_anterior(numero_serie, antes_id=relatorio_id)
    })


@app.route("/novo")
@app.route("/relatorio/novo")
@app.route("/novo_relatorio")
def novo_relatorio():
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio

    return render_template(
        "novo.html",
        contador_anterior="",
        codigos_pecas=codigos_pecas_utilizados(),
    )


@app.route("/criar_relatorio", methods=["POST"])
def criar_relatorio():
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio

    erro = validar_relatorio(request.form)
    if erro:
        return erro, 400

    assinatura_cliente, erro_assinatura = assinatura_do_formulario(request.form)
    if erro_assinatura:
        return erro_assinatura, 400

    relatorio = Relatorio(
        cliente=clean(request.form.get("cliente")),
        responsavel=clean(request.form.get("responsavel")),
        telefone=clean(request.form.get("telefone")),
        endereco=clean(request.form.get("endereco")),
        cep=formatar_cep(request.form.get("cep")),
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
        pecas=salvar_pecas(request.form),
        status=clean(request.form.get("status")) or "Concluido",
        tecnico=clean(request.form.get("tecnico")),
        observacoes=clean(request.form.get("observacoes")),
        assinatura_cliente=assinatura_cliente,
        token_compartilhamento=novo_token_compartilhamento(),
    )

    db.session.add(relatorio)
    db.session.commit()

    return redirect(url_for("ver_relatorio", relatorio_id=relatorio.id))


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

        assinatura_cliente, erro_assinatura = assinatura_do_formulario(request.form)
        if erro_assinatura:
            return erro_assinatura, 400

        relatorio.cliente = clean(request.form.get("cliente"))
        relatorio.responsavel = clean(request.form.get("responsavel"))
        relatorio.telefone = clean(request.form.get("telefone"))
        relatorio.endereco = clean(request.form.get("endereco"))
        relatorio.cep = formatar_cep(request.form.get("cep"))
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
        relatorio.pecas = salvar_pecas(request.form)
        relatorio.status = clean(request.form.get("status")) or "Concluido"
        relatorio.tecnico = clean(request.form.get("tecnico"))
        relatorio.observacoes = clean(request.form.get("observacoes"))
        relatorio.assinatura_cliente = assinatura_cliente

        db.session.commit()
        return redirect(url_for("admin"))

    pecas = ler_pecas(relatorio.pecas)
    itens_pecas = pecas["itens"]
    if pecas["legado"]:
        itens_pecas = [{"status": "", "quantidade": "", "descricao": pecas["legado"], "codigo": ""}]

    return render_template(
        "editar.html",
        relatorio=relatorio,
        itens_pecas=itens_pecas,
        contador_anterior=buscar_contador_anterior(relatorio.numero_serie, antes_id=relatorio.id),
        codigos_pecas=codigos_pecas_utilizados(),
    )


@app.route("/relatorio/<int:relatorio_id>")
@app.route("/ver_relatorio/<int:relatorio_id>")
def ver_relatorio(relatorio_id):
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio

    relatorio = Relatorio.query.get_or_404(relatorio_id)
    pecas = ler_pecas(relatorio.pecas)
    return render_template(
        "relatorio.html",
        relatorio=relatorio,
        pecas_relatorio=pecas["itens"],
        pecas_legadas=pecas["legado"],
        contador_anterior=buscar_contador_anterior(relatorio.numero_serie, antes_id=relatorio.id),
    )


@app.route("/compartilhado/<token>")
def relatorio_compartilhado(token):
    relatorio = Relatorio.query.filter_by(token_compartilhamento=token).first_or_404()
    pecas = ler_pecas(relatorio.pecas)
    return render_template(
        "relatorio.html",
        relatorio=relatorio,
        pecas_relatorio=pecas["itens"],
        pecas_legadas=pecas["legado"],
        contador_anterior=buscar_contador_anterior(relatorio.numero_serie, antes_id=relatorio.id),
        modo_compartilhado=True,
    )


@app.route("/relatorio/<int:relatorio_id>/whatsapp")
def enviar_relatorio_whatsapp(relatorio_id):
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio

    relatorio = Relatorio.query.get_or_404(relatorio_id)
    telefone = apenas_numeros(relatorio.telefone)
    if len(telefone) not in (10, 11):
        return "O telefone do cliente precisa ter DDD e 10 ou 11 numeros.", 400

    caminho_relatorio = url_for(
        "relatorio_compartilhado",
        token=relatorio.token_compartilhamento,
        _external=False,
    )
    base_publica = (
        os.getenv("PUBLIC_BASE_URL")
        or os.getenv("RENDER_EXTERNAL_URL")
        or request.url_root
    ).rstrip("/")
    link_relatorio = f"{base_publica}{caminho_relatorio}"
    mensagem = (
        f"Ola, {relatorio.responsavel or relatorio.cliente}! Segue o relatorio tecnico "
        f"do atendimento #{relatorio.id}: {link_relatorio}"
    )
    destino = f"https://wa.me/55{telefone}?{urlencode({'text': mensagem})}"
    return redirect(destino)


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
