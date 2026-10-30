from app import Relatorio, app, db, inicializar_banco


def _to_dict(relatorio):
    return {
        "id": relatorio.id,
        "cliente": relatorio.cliente,
        "telefone": relatorio.telefone,
        "responsavel": relatorio.responsavel,
        "endereco": relatorio.endereco,
        "cidade": relatorio.cidade,
        "bairro": relatorio.bairro,
        "cep": relatorio.cep,
        "uf": relatorio.uf,
        "marca": relatorio.marca,
        "modelo": relatorio.equipamento,
        "equipamento": relatorio.equipamento,
        "numero_serie": relatorio.numero_serie,
        "contador_geral": relatorio.contador_geral,
        "motivo": relatorio.defeito_relatado,
        "defeito_relatado": relatorio.defeito_relatado,
        "diagnostico": relatorio.diagnostico,
        "servico_executado": relatorio.servico_executado,
        "pecas": relatorio.pecas,
        "status": relatorio.status,
        "tecnico": relatorio.tecnico,
        "observacoes": relatorio.observacoes,
        "assinatura_cliente": relatorio.assinatura_cliente,
        "hora_inicio": relatorio.hora_inicio,
        "hora_fim": relatorio.hora_fim,
        "criado_em": relatorio.criado_em,
    }


def get_relatorios():
    with app.app_context():
        inicializar_banco()
        return [_to_dict(item) for item in Relatorio.query.order_by(Relatorio.id.desc()).all()]


def get_relatorio_by_id(relatorio_id):
    with app.app_context():
        inicializar_banco()
        relatorio = Relatorio.query.get(relatorio_id)
        return _to_dict(relatorio) if relatorio else None


def create_relatorio(data):
    with app.app_context():
        inicializar_banco()
        relatorio = Relatorio(
            cliente=data.get("cliente"),
            telefone=data.get("telefone"),
            responsavel=data.get("responsavel"),
            endereco=data.get("endereco"),
            cidade=data.get("cidade"),
            bairro=data.get("bairro"),
            cep=data.get("cep"),
            uf=data.get("uf"),
            marca=data.get("marca") or "Konica Minolta",
            equipamento=data.get("equipamento") or data.get("modelo"),
            numero_serie=data.get("numero_serie"),
            contador_geral=data.get("contador_geral"),
            defeito_relatado=data.get("defeito_relatado") or data.get("motivo"),
            diagnostico=data.get("diagnostico"),
            servico_executado=data.get("servico_executado"),
            pecas=data.get("pecas"),
            status=data.get("status") or "Concluido",
            tecnico=data.get("tecnico"),
            observacoes=data.get("observacoes"),
            assinatura_cliente=data.get("assinatura_cliente"),
            hora_inicio=data.get("hora_inicio"),
            hora_fim=data.get("hora_fim"),
        )
        db.session.add(relatorio)
        db.session.commit()
        return relatorio.id


def update_relatorio(relatorio_id, data):
    with app.app_context():
        inicializar_banco()
        relatorio = Relatorio.query.get_or_404(relatorio_id)
        relatorio.cliente = data.get("cliente")
        relatorio.telefone = data.get("telefone")
        relatorio.responsavel = data.get("responsavel")
        relatorio.endereco = data.get("endereco")
        relatorio.cidade = data.get("cidade")
        relatorio.bairro = data.get("bairro")
        relatorio.cep = data.get("cep")
        relatorio.uf = data.get("uf")
        relatorio.marca = data.get("marca") or "Konica Minolta"
        relatorio.equipamento = data.get("equipamento") or data.get("modelo")
        relatorio.numero_serie = data.get("numero_serie")
        relatorio.contador_geral = data.get("contador_geral")
        relatorio.defeito_relatado = data.get("defeito_relatado") or data.get("motivo")
        relatorio.diagnostico = data.get("diagnostico")
        relatorio.servico_executado = data.get("servico_executado")
        relatorio.pecas = data.get("pecas")
        relatorio.status = data.get("status") or "Concluido"
        relatorio.tecnico = data.get("tecnico")
        relatorio.observacoes = data.get("observacoes")
        if "assinatura_cliente" in data:
            relatorio.assinatura_cliente = data.get("assinatura_cliente")
        relatorio.hora_inicio = data.get("hora_inicio")
        relatorio.hora_fim = data.get("hora_fim")
        db.session.commit()


def delete_relatorio(relatorio_id):
    with app.app_context():
        inicializar_banco()
        relatorio = Relatorio.query.get_or_404(relatorio_id)
        db.session.delete(relatorio)
        db.session.commit()
