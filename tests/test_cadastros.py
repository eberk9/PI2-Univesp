"""Testes das funcoes do sindico: cadastros (RF02, RF03) e painel (RF12)."""
import pytest

from tests.conftest import autenticar


@pytest.fixture
def sindico_logado(client):
    autenticar(client, "sindico@teste.local")
    return client


def novo_usuario(client, **extra):
    corpo = {
        "nome": "Joana Lima",
        "email": "joana@teste.local",
        "senha": "senha-forte",
        "perfil": "PORTEIRO",
    }
    corpo.update(extra)
    return client.post("/api/v1/usuarios", json=corpo)


# --------------------------------------------------------------------- RF02
def test_sindico_cadastra_unidade(sindico_logado):
    resposta = sindico_logado.post(
        "/api/v1/unidades", json={"bloco": " c ", "numero": "303", "descricao": "Cobertura"}
    )
    assert resposta.status_code == 201
    assert resposta.get_json()["identificacao"] == "C 303"


def test_unidade_repetida_e_recusada(sindico_logado):
    resposta = sindico_logado.post("/api/v1/unidades", json={"bloco": "A", "numero": "101"})
    assert resposta.status_code == 409


def test_unidade_sem_numero_e_recusada(sindico_logado):
    assert sindico_logado.post("/api/v1/unidades", json={"bloco": "A"}).status_code == 400


def test_porteiro_nao_cadastra_unidade(porteiro_logado):
    resposta = porteiro_logado.post("/api/v1/unidades", json={"numero": "999"})
    assert resposta.status_code == 403


# --------------------------------------------------------------------- RF03
def test_sindico_cadastra_porteiro_que_consegue_entrar(sindico_logado, client):
    assert novo_usuario(sindico_logado).status_code == 201
    client.get("/logout")
    assert autenticar(client, "joana@teste.local", "senha-forte").status_code == 201


def test_morador_precisa_de_unidade(sindico_logado, unidade_id):
    assert novo_usuario(sindico_logado, perfil="MORADOR").status_code == 400
    resposta = novo_usuario(sindico_logado, perfil="MORADOR", unidade_id=unidade_id)
    assert resposta.status_code == 201
    assert resposta.get_json()["unidade"] == "A 101"


def test_perfil_fora_da_lista_e_recusado(sindico_logado):
    assert novo_usuario(sindico_logado, perfil="ADMIN").status_code == 400


def test_senha_curta_e_recusada(sindico_logado):
    assert novo_usuario(sindico_logado, senha="123").status_code == 400


def test_email_repetido_e_recusado(sindico_logado):
    assert novo_usuario(sindico_logado, email="PORTEIRO@teste.local").status_code == 409


def test_desativar_e_reativar_usuario(sindico_logado, client):
    usuario_id = novo_usuario(sindico_logado).get_json()["id"]
    resposta = sindico_logado.patch(f"/api/v1/usuarios/{usuario_id}", json={"ativo": False})
    assert resposta.get_json()["ativo"] is False

    client.get("/logout")
    assert autenticar(client, "joana@teste.local", "senha-forte").status_code == 403


def test_sindico_nao_desativa_a_si_mesmo(sindico_logado):
    meu_id = sindico_logado.get("/api/v1/sessoes/atual").get_json()["usuario"]["id"]
    resposta = sindico_logado.patch(f"/api/v1/usuarios/{meu_id}", json={"ativo": False})
    assert resposta.status_code == 400


def test_redefinir_senha(sindico_logado, client):
    usuario_id = novo_usuario(sindico_logado).get_json()["id"]
    sindico_logado.patch(f"/api/v1/usuarios/{usuario_id}", json={"senha": "outra-senha"})
    client.get("/logout")
    assert autenticar(client, "joana@teste.local", "outra-senha").status_code == 201


def test_porteiro_nao_ve_usuarios(porteiro_logado):
    assert porteiro_logado.get("/api/v1/usuarios").status_code == 403


# --------------------------------------------------------------------- RF12
def test_sindico_entra_pelo_painel(client):
    autenticar(client, "sindico@teste.local")
    resposta = client.get("/")
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/painel")


def test_paginas_do_sindico_sao_exclusivas(porteiro_logado):
    assert porteiro_logado.get("/painel").status_code == 403
    assert porteiro_logado.get("/cadastros").status_code == 403


def test_indicadores_contam_devolvidas(sindico_logado, unidade_id):
    encomenda = sindico_logado.post(
        "/api/v1/encomendas",
        json={"codigo_rastreio": "DV1", "unidade_id": unidade_id, "destinatario": "Ana"},
    ).get_json()
    sindico_logado.post(f"/api/v1/encomendas/{encomenda['id']}/devolucao", json={})
    assert sindico_logado.get("/api/v1/indicadores").get_json()["devolvidas"] == 1
