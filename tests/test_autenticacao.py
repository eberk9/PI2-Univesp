"""Testes de autenticacao e de controle de acesso (RF01)."""
from tests.conftest import autenticar


def test_login_com_credenciais_validas(client):
    resposta = autenticar(client, "porteiro@teste.local")
    assert resposta.status_code == 201
    assert resposta.get_json()["usuario"]["perfil"] == "PORTEIRO"


def test_login_com_senha_errada(client):
    resposta = autenticar(client, "porteiro@teste.local", "errada")
    assert resposta.status_code == 401


def test_login_com_email_inexistente(client):
    resposta = autenticar(client, "ninguem@teste.local")
    assert resposta.status_code == 401


def test_usuario_inativo_nao_entra(client):
    resposta = autenticar(client, "inativo@teste.local")
    assert resposta.status_code == 403


def test_senha_nao_e_guardada_em_texto_claro(app):
    """RNF03: a senha so pode existir como hash."""
    from app.extensions import db
    from app.models import Usuario

    usuario = db.session.scalar(
        db.select(Usuario).filter_by(email="porteiro@teste.local")
    )
    assert usuario.senha_hash != "senha123"
    assert "senha123" not in usuario.senha_hash
    assert usuario.conferir_senha("senha123")


def test_api_exige_autenticacao(client):
    resposta = client.get("/api/v1/encomendas")
    assert resposta.status_code == 401
    assert "erro" in resposta.get_json()


def test_logout_encerra_a_sessao(porteiro_logado):
    assert porteiro_logado.delete("/api/v1/sessoes").status_code == 204
    assert porteiro_logado.get("/api/v1/encomendas").status_code == 401


def test_pagina_protegida_redireciona_para_login(client):
    resposta = client.get("/encomendas/pendentes")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]
