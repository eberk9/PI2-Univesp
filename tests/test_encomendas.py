"""Testes das funcionalidades criticas: registro, baixa e historico."""


def registrar(client, unidade_id, codigo="AA111222333BR", **extra):
    corpo = {
        "codigo_rastreio": codigo,
        "unidade_id": unidade_id,
        "destinatario": "Ana Ribeiro",
    }
    corpo.update(extra)
    return client.post("/api/v1/encomendas", json=corpo)


# --------------------------------------------------------------- RF04, RF05
def test_registrar_encomenda(porteiro_logado, unidade_id):
    resposta = registrar(porteiro_logado, unidade_id)
    assert resposta.status_code == 201

    dados = resposta.get_json()
    assert dados["codigo_rastreio"] == "AA111222333BR"
    assert dados["situacao"] == "RECEBIDA"
    # RF05: o porteiro vem da sessao, nao do formulario
    assert dados["recebida_por"] == "Porteiro de Teste"
    assert dados["recebida_em"] is not None


def test_codigo_de_rastreio_e_normalizado(porteiro_logado, unidade_id):
    resposta = registrar(porteiro_logado, unidade_id, codigo="  aa999888777br  ")
    assert resposta.get_json()["codigo_rastreio"] == "AA999888777BR"


def test_registro_sem_codigo_e_rejeitado(porteiro_logado, unidade_id):
    resposta = registrar(porteiro_logado, unidade_id, codigo="   ")
    assert resposta.status_code == 400


def test_registro_sem_destinatario_e_rejeitado(porteiro_logado, unidade_id):
    resposta = registrar(porteiro_logado, unidade_id, destinatario="")
    assert resposta.status_code == 400


def test_registro_em_unidade_inexistente(porteiro_logado):
    resposta = registrar(porteiro_logado, 9999)
    assert resposta.status_code == 404


def test_nao_registra_duas_vezes_o_mesmo_pacote_pendente(porteiro_logado, unidade_id):
    assert registrar(porteiro_logado, unidade_id).status_code == 201
    repetida = registrar(porteiro_logado, unidade_id)
    assert repetida.status_code == 409


def test_morador_nao_pode_registrar(morador_logado, unidade_id):
    assert registrar(morador_logado, unidade_id).status_code == 403


# --------------------------------------------------------------------- RF08
def test_dar_baixa_na_retirada(porteiro_logado, unidade_id):
    encomenda_id = registrar(porteiro_logado, unidade_id).get_json()["id"]

    resposta = porteiro_logado.post(
        f"/api/v1/encomendas/{encomenda_id}/retirada",
        json={"retirada_por_nome": "Ana Ribeiro"},
    )
    assert resposta.status_code == 200

    dados = resposta.get_json()
    assert dados["situacao"] == "RETIRADA"
    assert dados["retirada_por_nome"] == "Ana Ribeiro"
    assert dados["entregue_por"] == "Porteiro de Teste"
    assert dados["retirada_em"] is not None


def test_baixa_sem_informar_quem_retirou(porteiro_logado, unidade_id):
    encomenda_id = registrar(porteiro_logado, unidade_id).get_json()["id"]
    resposta = porteiro_logado.post(
        f"/api/v1/encomendas/{encomenda_id}/retirada",
        json={"retirada_por_nome": "  "},
    )
    assert resposta.status_code == 400


def test_nao_da_baixa_duas_vezes(porteiro_logado, unidade_id):
    encomenda_id = registrar(porteiro_logado, unidade_id).get_json()["id"]
    caminho = f"/api/v1/encomendas/{encomenda_id}/retirada"
    porteiro_logado.post(caminho, json={"retirada_por_nome": "Ana"})
    repetida = porteiro_logado.post(caminho, json={"retirada_por_nome": "Outra"})
    assert repetida.status_code == 409


def test_baixa_em_encomenda_inexistente(porteiro_logado):
    resposta = porteiro_logado.post(
        "/api/v1/encomendas/9999/retirada", json={"retirada_por_nome": "Ana"}
    )
    assert resposta.status_code == 404


# ------------------------------------------------------- RF10 e RNF05
def test_historico_registra_recebimento_e_retirada(porteiro_logado, unidade_id):
    encomenda_id = registrar(porteiro_logado, unidade_id).get_json()["id"]
    porteiro_logado.post(
        f"/api/v1/encomendas/{encomenda_id}/retirada",
        json={"retirada_por_nome": "Ana Ribeiro"},
    )

    dados = porteiro_logado.get(f"/api/v1/encomendas/{encomenda_id}").get_json()
    tipos = [m["tipo"] for m in dados["movimentacoes"]]
    assert tipos == ["RECEBIMENTO", "RETIRADA"]
    assert "Ana Ribeiro" in dados["movimentacoes"][1]["descricao"]


def test_historico_nao_e_sobrescrito_pela_devolucao(porteiro_logado, unidade_id):
    """RNF05: movimentacoes sao acrescentadas, nunca substituidas."""
    encomenda_id = registrar(porteiro_logado, unidade_id).get_json()["id"]
    porteiro_logado.post(
        f"/api/v1/encomendas/{encomenda_id}/devolucao",
        json={"motivo": "Nao retirada em 15 dias."},
    )

    dados = porteiro_logado.get(f"/api/v1/encomendas/{encomenda_id}").get_json()
    assert dados["situacao"] == "DEVOLVIDA"
    assert len(dados["movimentacoes"]) == 2
    assert dados["movimentacoes"][0]["tipo"] == "RECEBIMENTO"


# --------------------------------------------------------------- RF06, RF07
def test_listar_filtrando_por_situacao(porteiro_logado, unidade_id):
    registrar(porteiro_logado, unidade_id, codigo="AAA")
    segunda = registrar(porteiro_logado, unidade_id, codigo="BBB").get_json()["id"]
    porteiro_logado.post(
        f"/api/v1/encomendas/{segunda}/retirada", json={"retirada_por_nome": "Ana"}
    )

    pendentes = porteiro_logado.get("/api/v1/encomendas?situacao=RECEBIDA").get_json()
    assert pendentes["total"] == 1
    assert pendentes["encomendas"][0]["codigo_rastreio"] == "AAA"

    retiradas = porteiro_logado.get("/api/v1/encomendas?situacao=RETIRADA").get_json()
    assert retiradas["total"] == 1


def test_situacao_invalida_no_filtro(porteiro_logado):
    assert porteiro_logado.get("/api/v1/encomendas?situacao=SUMIU").status_code == 400


def test_busca_por_codigo_e_por_destinatario(porteiro_logado, unidade_id):
    registrar(porteiro_logado, unidade_id, codigo="XY123", destinatario="Ana Ribeiro")
    registrar(porteiro_logado, unidade_id, codigo="ZW999", destinatario="Carlos Menezes")

    por_codigo = porteiro_logado.get("/api/v1/encomendas?q=XY1").get_json()
    assert por_codigo["total"] == 1
    assert por_codigo["encomendas"][0]["codigo_rastreio"] == "XY123"

    por_nome = porteiro_logado.get("/api/v1/encomendas?q=Carlos").get_json()
    assert por_nome["total"] == 1
    assert por_nome["encomendas"][0]["destinatario"] == "Carlos Menezes"


# --------------------------------------------------------------------- RF11
def test_morador_so_ve_a_propria_unidade(
    client, porteiro_logado, unidade_id, unidade_b_id
):
    registrar(porteiro_logado, unidade_id, codigo="DAMINHA")
    registrar(porteiro_logado, unidade_b_id, codigo="DOVIZINHO")
    porteiro_logado.delete("/api/v1/sessoes")

    client.post(
        "/api/v1/sessoes",
        json={"email": "morador@teste.local", "senha": "senha123"},
    )
    dados = client.get("/api/v1/encomendas").get_json()
    assert dados["total"] == 1
    assert dados["encomendas"][0]["codigo_rastreio"] == "DAMINHA"


def test_morador_nao_abre_encomenda_de_outra_unidade(
    client, porteiro_logado, unidade_b_id
):
    alheia = registrar(porteiro_logado, unidade_b_id, codigo="DOVIZINHO").get_json()["id"]
    porteiro_logado.delete("/api/v1/sessoes")

    client.post(
        "/api/v1/sessoes",
        json={"email": "morador@teste.local", "senha": "senha123"},
    )
    assert client.get(f"/api/v1/encomendas/{alheia}").status_code == 403


# --------------------------------------------------------------------- RF12
def test_indicadores(porteiro_logado, unidade_id):
    registrar(porteiro_logado, unidade_id, codigo="PENDENTE")
    retirada = registrar(porteiro_logado, unidade_id, codigo="RETIRADA").get_json()["id"]
    porteiro_logado.post(
        f"/api/v1/encomendas/{retirada}/retirada", json={"retirada_por_nome": "Ana"}
    )

    dados = porteiro_logado.get("/api/v1/indicadores").get_json()
    assert dados["pendentes"] == 1
    assert dados["retiradas"] == 1
    assert dados["tempo_medio_retirada_horas"] is not None
