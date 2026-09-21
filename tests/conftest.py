"""Configuracao comum dos testes: aplicacao em memoria e usuarios de apoio."""
import pytest

from app import create_app
from app.extensions import db as _db
from app.models import (
    PERFIL_MORADOR,
    PERFIL_PORTEIRO,
    PERFIL_SINDICO,
    Transportadora,
    Unidade,
    Usuario,
)


@pytest.fixture
def app():
    aplicacao = create_app("config.TestConfig")
    with aplicacao.app_context():
        _db.create_all()
        _semear()
        yield aplicacao
        _db.session.remove()
        _db.drop_all()


def _semear():
    unidade_a = Unidade(bloco="A", numero="101")
    unidade_b = Unidade(bloco="B", numero="202")
    _db.session.add_all([unidade_a, unidade_b])

    _db.session.add(Transportadora(nome="Correios"))

    porteiro = Usuario(
        nome="Porteiro de Teste", email="porteiro@teste.local", perfil=PERFIL_PORTEIRO
    )
    porteiro.definir_senha("senha123")

    sindico = Usuario(
        nome="Sindico de Teste", email="sindico@teste.local", perfil=PERFIL_SINDICO
    )
    sindico.definir_senha("senha123")

    morador = Usuario(
        nome="Morador de Teste",
        email="morador@teste.local",
        perfil=PERFIL_MORADOR,
        unidade=unidade_a,
    )
    morador.definir_senha("senha123")

    inativo = Usuario(
        nome="Ex-porteiro", email="inativo@teste.local", perfil=PERFIL_PORTEIRO,
        ativo=False,
    )
    inativo.definir_senha("senha123")

    _db.session.add_all([porteiro, sindico, morador, inativo])
    _db.session.commit()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db


def autenticar(client, email, senha="senha123"):
    """Abre sessao pela API e devolve a resposta."""
    return client.post(
        "/api/v1/sessoes", json={"email": email, "senha": senha}
    )


@pytest.fixture
def porteiro_logado(client):
    autenticar(client, "porteiro@teste.local")
    return client


@pytest.fixture
def morador_logado(client):
    autenticar(client, "morador@teste.local")
    return client


@pytest.fixture
def unidade_id(app):
    return _db.session.scalar(
        _db.select(Unidade.id).filter_by(bloco="A", numero="101")
    )


@pytest.fixture
def unidade_b_id(app):
    return _db.session.scalar(
        _db.select(Unidade.id).filter_by(bloco="B", numero="202")
    )
