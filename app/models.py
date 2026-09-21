"""Modelos de dados do sistema de controle de encomendas.

O esquema segue o Apendice A do Relatorio Parcial: cinco entidades, com o
historico de cada encomenda preservado na tabela de movimentacoes.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager

# O sistema atende uma unica portaria, em Piracicaba/SP. Gravamos o horario
# local dela: o servidor de producao roda em UTC, e tanto o template quanto o
# JavaScript exibem o valor como veio, sem converter. Usar UTC aqui faria a
# portaria ver todos os horarios 3 horas adiantados.
FUSO = ZoneInfo("America/Sao_Paulo")


def agora():
    """Momento atual no fuso da portaria, sem tzinfo (compativel com MySQL)."""
    return datetime.now(FUSO).replace(tzinfo=None)


# Perfis de usuario
PERFIL_PORTEIRO = "PORTEIRO"
PERFIL_MORADOR = "MORADOR"
PERFIL_SINDICO = "SINDICO"
PERFIS = (PERFIL_PORTEIRO, PERFIL_MORADOR, PERFIL_SINDICO)

# Situacoes da encomenda
SITUACAO_RECEBIDA = "RECEBIDA"
SITUACAO_RETIRADA = "RETIRADA"
SITUACAO_DEVOLVIDA = "DEVOLVIDA"
SITUACOES = (SITUACAO_RECEBIDA, SITUACAO_RETIRADA, SITUACAO_DEVOLVIDA)

# Tipos de movimentacao
MOV_RECEBIMENTO = "RECEBIMENTO"
MOV_AVISO_MORADOR = "AVISO_MORADOR"
MOV_RETIRADA = "RETIRADA"
MOV_DEVOLUCAO = "DEVOLUCAO"
MOV_OBSERVACAO = "OBSERVACAO"


class Unidade(db.Model):
    __tablename__ = "unidade"

    id = db.Column(db.Integer, primary_key=True)
    bloco = db.Column(db.String(20), nullable=False, default="")
    numero = db.Column(db.String(20), nullable=False)
    descricao = db.Column(db.String(120), nullable=False, default="")

    __table_args__ = (db.UniqueConstraint("bloco", "numero", name="uq_unidade"),)

    @property
    def identificacao(self):
        return f"{self.bloco} {self.numero}".strip()

    def to_dict(self):
        return {
            "id": self.id,
            "bloco": self.bloco,
            "numero": self.numero,
            "descricao": self.descricao,
            "identificacao": self.identificacao,
        }

    def __repr__(self):
        return f"<Unidade {self.identificacao}>"


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.String(20), nullable=False, default=PERFIL_PORTEIRO)
    unidade_id = db.Column(db.Integer, db.ForeignKey("unidade.id"), nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    unidade = db.relationship("Unidade", backref="moradores")

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def conferir_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_active(self):
        return self.ativo

    def e_porteiro(self):
        return self.perfil == PERFIL_PORTEIRO

    def e_sindico(self):
        return self.perfil == PERFIL_SINDICO

    def e_morador(self):
        return self.perfil == PERFIL_MORADOR

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "perfil": self.perfil,
            "unidade_id": self.unidade_id,
        }

    def __repr__(self):
        return f"<Usuario {self.email} ({self.perfil})>"


class Transportadora(db.Model):
    __tablename__ = "transportadora"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False, unique=True)

    def to_dict(self):
        return {"id": self.id, "nome": self.nome}

    def __repr__(self):
        return f"<Transportadora {self.nome}>"


class Encomenda(db.Model):
    __tablename__ = "encomenda"

    id = db.Column(db.Integer, primary_key=True)
    codigo_rastreio = db.Column(db.String(60), nullable=False, index=True)
    unidade_id = db.Column(db.Integer, db.ForeignKey("unidade.id"), nullable=False)
    destinatario = db.Column(db.String(120), nullable=False)
    transportadora_id = db.Column(
        db.Integer, db.ForeignKey("transportadora.id"), nullable=True
    )
    situacao = db.Column(
        db.String(20), nullable=False, default=SITUACAO_RECEBIDA, index=True
    )
    observacao = db.Column(db.String(255), nullable=False, default="")

    recebida_em = db.Column(db.DateTime, nullable=False, default=agora)
    recebida_por_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)

    retirada_em = db.Column(db.DateTime, nullable=True)
    retirada_por_nome = db.Column(db.String(120), nullable=True)
    entregue_por_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=True)

    unidade = db.relationship("Unidade", backref="encomendas")
    transportadora = db.relationship("Transportadora")
    recebida_por = db.relationship("Usuario", foreign_keys=[recebida_por_id])
    entregue_por = db.relationship("Usuario", foreign_keys=[entregue_por_id])
    movimentacoes = db.relationship(
        "Movimentacao",
        backref="encomenda",
        order_by="Movimentacao.ocorrida_em",
        cascade="all, delete-orphan",
    )

    __table_args__ = (db.Index("ix_encomenda_unidade_situacao", "unidade_id", "situacao"),)

    @property
    def pendente(self):
        return self.situacao == SITUACAO_RECEBIDA

    def to_dict(self, incluir_movimentacoes=False):
        dados = {
            "id": self.id,
            "codigo_rastreio": self.codigo_rastreio,
            "situacao": self.situacao,
            "destinatario": self.destinatario,
            "observacao": self.observacao,
            "unidade": self.unidade.to_dict() if self.unidade else None,
            "transportadora": (
                self.transportadora.to_dict() if self.transportadora else None
            ),
            "recebida_em": self.recebida_em.isoformat() if self.recebida_em else None,
            "recebida_por": (
                self.recebida_por.nome if self.recebida_por else None
            ),
            "retirada_em": self.retirada_em.isoformat() if self.retirada_em else None,
            "retirada_por_nome": self.retirada_por_nome,
            "entregue_por": self.entregue_por.nome if self.entregue_por else None,
        }
        if incluir_movimentacoes:
            dados["movimentacoes"] = [m.to_dict() for m in self.movimentacoes]
        return dados

    def __repr__(self):
        return f"<Encomenda {self.codigo_rastreio} ({self.situacao})>"


class Movimentacao(db.Model):
    """Historico da encomenda. Linhas sao acrescentadas, nunca alteradas."""

    __tablename__ = "movimentacao"

    id = db.Column(db.Integer, primary_key=True)
    encomenda_id = db.Column(
        db.Integer, db.ForeignKey("encomenda.id"), nullable=False, index=True
    )
    tipo = db.Column(db.String(20), nullable=False)
    ocorrida_em = db.Column(db.DateTime, nullable=False, default=agora)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=True)
    descricao = db.Column(db.String(255), nullable=False, default="")

    usuario = db.relationship("Usuario")

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "ocorrida_em": self.ocorrida_em.isoformat() if self.ocorrida_em else None,
            "usuario": self.usuario.nome if self.usuario else None,
            "descricao": self.descricao,
        }

    def __repr__(self):
        return f"<Movimentacao {self.tipo} enc={self.encomenda_id}>"


def registrar_movimentacao(encomenda, tipo, usuario=None, descricao=""):
    """Acrescenta uma linha ao historico da encomenda."""
    mov = Movimentacao(
        encomenda=encomenda,
        tipo=tipo,
        usuario=usuario,
        descricao=descricao,
    )
    db.session.add(mov)
    return mov


@login_manager.user_loader
def carregar_usuario(user_id):
    return db.session.get(Usuario, int(user_id))
