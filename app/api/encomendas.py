"""Recursos de encomenda: listagem, registro, retirada e devolucao."""
from datetime import datetime

from flask import jsonify, request
from flask_login import current_user

from app.api import api_bp, erro, exige_login, exige_perfil
from app.extensions import db
from app.models import (
    MOV_DEVOLUCAO,
    MOV_RECEBIMENTO,
    MOV_RETIRADA,
    PERFIL_PORTEIRO,
    PERFIL_SINDICO,
    SITUACAO_DEVOLVIDA,
    SITUACAO_RECEBIDA,
    SITUACAO_RETIRADA,
    SITUACOES,
    Encomenda,
    Transportadora,
    Unidade,
    agora,
    registrar_movimentacao,
)


def _data(texto):
    """Converte 'AAAA-MM-DD' em datetime; devolve None se invalido."""
    try:
        return datetime.strptime(texto, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


@api_bp.get("/encomendas")
@exige_login
def listar_encomendas():
    consulta = db.select(Encomenda)

    # Morador so enxerga o que e destinado a sua unidade.
    if current_user.e_morador():
        if current_user.unidade_id is None:
            return jsonify({"encomendas": [], "total": 0})
        consulta = consulta.filter_by(unidade_id=current_user.unidade_id)
    elif request.args.get("unidade"):
        consulta = consulta.filter_by(unidade_id=request.args.get("unidade", type=int))

    situacao = (request.args.get("situacao") or "").upper()
    if situacao:
        if situacao not in SITUACOES:
            return erro(f"Situacao invalida: {situacao}.", 400)
        consulta = consulta.filter_by(situacao=situacao)

    de = _data(request.args.get("de"))
    if de:
        consulta = consulta.filter(Encomenda.recebida_em >= de)
    ate = _data(request.args.get("ate"))
    if ate:
        consulta = consulta.filter(Encomenda.recebida_em < ate.replace(hour=23, minute=59, second=59))

    termo = (request.args.get("q") or "").strip()
    if termo:
        curinga = f"%{termo}%"
        consulta = consulta.join(Unidade).filter(
            db.or_(
                Encomenda.codigo_rastreio.ilike(curinga),
                Encomenda.destinatario.ilike(curinga),
                Unidade.numero.ilike(curinga),
            )
        )

    encomendas = db.session.scalars(
        consulta.order_by(Encomenda.recebida_em.desc())
    ).all()
    return jsonify(
        {"encomendas": [e.to_dict() for e in encomendas], "total": len(encomendas)}
    )


@api_bp.post("/encomendas")
@exige_perfil(PERFIL_PORTEIRO, PERFIL_SINDICO)
def registrar_encomenda():
    dados = request.get_json(silent=True) or request.form

    codigo = (dados.get("codigo_rastreio") or "").strip().upper()
    if not codigo:
        return erro("Informe o codigo de rastreio.", 400)

    destinatario = (dados.get("destinatario") or "").strip()
    if not destinatario:
        return erro("Informe o destinatario.", 400)

    try:
        unidade_id = int(dados.get("unidade_id"))
    except (TypeError, ValueError):
        return erro("Informe a unidade de destino.", 400)

    unidade = db.session.get(Unidade, unidade_id)
    if unidade is None:
        return erro("Unidade nao encontrada.", 404)

    transportadora_id = dados.get("transportadora_id")
    if transportadora_id:
        try:
            transportadora_id = int(transportadora_id)
        except (TypeError, ValueError):
            return erro("Transportadora invalida.", 400)
        if db.session.get(Transportadora, transportadora_id) is None:
            return erro("Transportadora nao encontrada.", 404)
    else:
        transportadora_id = None

    # Evita registrar duas vezes o mesmo pacote ainda pendente.
    duplicada = db.session.scalar(
        db.select(Encomenda).filter_by(
            codigo_rastreio=codigo, situacao=SITUACAO_RECEBIDA
        )
    )
    if duplicada is not None:
        return erro(
            f"Ja existe encomenda pendente com o codigo {codigo} "
            f"(unidade {duplicada.unidade.identificacao}).",
            409,
        )

    encomenda = Encomenda(
        codigo_rastreio=codigo,
        unidade_id=unidade_id,
        destinatario=destinatario,
        transportadora_id=transportadora_id,
        observacao=(dados.get("observacao") or "").strip(),
        situacao=SITUACAO_RECEBIDA,
        recebida_em=agora(),
        recebida_por_id=current_user.id,
    )
    db.session.add(encomenda)
    db.session.flush()
    registrar_movimentacao(
        encomenda,
        MOV_RECEBIMENTO,
        usuario=current_user,
        descricao=f"Recebida na portaria para a unidade {unidade.identificacao}.",
    )
    db.session.commit()
    return jsonify(encomenda.to_dict(incluir_movimentacoes=True)), 201


@api_bp.get("/encomendas/<int:encomenda_id>")
@exige_login
def detalhar_encomenda(encomenda_id):
    encomenda = db.session.get(Encomenda, encomenda_id)
    if encomenda is None:
        return erro("Encomenda nao encontrada.", 404)
    if current_user.e_morador() and encomenda.unidade_id != current_user.unidade_id:
        return erro("Esta encomenda nao pertence a sua unidade.", 403)
    return jsonify(encomenda.to_dict(incluir_movimentacoes=True))


@api_bp.post("/encomendas/<int:encomenda_id>/retirada")
@exige_perfil(PERFIL_PORTEIRO, PERFIL_SINDICO)
def dar_baixa(encomenda_id):
    encomenda = db.session.get(Encomenda, encomenda_id)
    if encomenda is None:
        return erro("Encomenda nao encontrada.", 404)
    if encomenda.situacao != SITUACAO_RECEBIDA:
        return erro(
            f"Esta encomenda ja consta como {encomenda.situacao.lower()}.", 409
        )

    dados = request.get_json(silent=True) or request.form
    quem_retirou = (dados.get("retirada_por_nome") or "").strip()
    if not quem_retirou:
        return erro("Informe o nome de quem esta retirando.", 400)

    encomenda.situacao = SITUACAO_RETIRADA
    encomenda.retirada_em = agora()
    encomenda.retirada_por_nome = quem_retirou
    encomenda.entregue_por_id = current_user.id
    registrar_movimentacao(
        encomenda,
        MOV_RETIRADA,
        usuario=current_user,
        descricao=f"Retirada por {quem_retirou}.",
    )
    db.session.commit()
    return jsonify(encomenda.to_dict(incluir_movimentacoes=True))


@api_bp.post("/encomendas/<int:encomenda_id>/devolucao")
@exige_perfil(PERFIL_PORTEIRO, PERFIL_SINDICO)
def devolver(encomenda_id):
    encomenda = db.session.get(Encomenda, encomenda_id)
    if encomenda is None:
        return erro("Encomenda nao encontrada.", 404)
    if encomenda.situacao != SITUACAO_RECEBIDA:
        return erro(
            f"Esta encomenda ja consta como {encomenda.situacao.lower()}.", 409
        )

    dados = request.get_json(silent=True) or request.form
    motivo = (dados.get("motivo") or "Devolvida a transportadora.").strip()

    encomenda.situacao = SITUACAO_DEVOLVIDA
    registrar_movimentacao(
        encomenda, MOV_DEVOLUCAO, usuario=current_user, descricao=motivo
    )
    db.session.commit()
    return jsonify(encomenda.to_dict(incluir_movimentacoes=True))


@api_bp.get("/indicadores")
@exige_perfil(PERFIL_SINDICO, PERFIL_PORTEIRO)
def indicadores():
    pendentes = db.session.scalar(
        db.select(db.func.count(Encomenda.id)).filter_by(situacao=SITUACAO_RECEBIDA)
    )
    retiradas = db.session.scalars(
        db.select(Encomenda).filter_by(situacao=SITUACAO_RETIRADA)
    ).all()

    horas = [
        (e.retirada_em - e.recebida_em).total_seconds() / 3600
        for e in retiradas
        if e.retirada_em and e.recebida_em
    ]
    media = round(sum(horas) / len(horas), 1) if horas else None

    return jsonify(
        {
            "pendentes": pendentes,
            "retiradas": len(retiradas),
            "tempo_medio_retirada_horas": media,
        }
    )
