"""Cria as tabelas e popula o banco com dados de demonstracao.

    python seed.py

Todos os nomes sao ficticios. Dados reais de moradores nunca entram no
repositorio -- ver RNF04 (minimizacao, LGPD) no Relatorio Parcial.
"""
from datetime import timedelta

from app import create_app
from app.extensions import db
from app.models import (
    MOV_RECEBIMENTO,
    MOV_RETIRADA,
    PERFIL_MORADOR,
    PERFIL_PORTEIRO,
    PERFIL_SINDICO,
    SITUACAO_RECEBIDA,
    SITUACAO_RETIRADA,
    Encomenda,
    Transportadora,
    Unidade,
    Usuario,
    agora,
    registrar_movimentacao,
)

UNIDADES = [
    ("A", "101", "Apartamento térreo"),
    ("A", "102", ""),
    ("A", "201", ""),
    ("B", "101", ""),
    ("B", "102", "Esquina"),
    ("B", "201", ""),
]

TRANSPORTADORAS = ["Correios", "Jadlog", "Loggi", "Total Express", "Outra"]

USUARIOS = [
    ("Marcelino da Silva", "marcelino@portaria.local", "portaria123", PERFIL_PORTEIRO, None),
    ("Enivaldo Souza", "enivaldo@portaria.local", "portaria123", PERFIL_PORTEIRO, None),
    ("Sindico do Residencial", "sindico@portaria.local", "sindico123", PERFIL_SINDICO, None),
    ("Ana Ribeiro", "ana@morador.local", "morador123", PERFIL_MORADOR, ("A", "101")),
    ("Carlos Menezes", "carlos@morador.local", "morador123", PERFIL_MORADOR, ("B", "102")),
]

ENCOMENDAS = [
    # (codigo, bloco, numero, destinatario, transportadora, horas_atras, retirada_por)
    ("AA123456789BR", "A", "101", "Ana Ribeiro", "Correios", 30, "Ana Ribeiro"),
    ("BB987654321BR", "A", "101", "Ana Ribeiro", "Jadlog", 6, None),
    ("LG0099887766", "B", "102", "Carlos Menezes", "Loggi", 20, None),
    ("TE5544332211", "A", "201", "Marina Costa", "Total Express", 50, "Marina Costa"),
    ("AA555666777BR", "B", "201", "Joao Pedro Alves", "Correios", 3, None),
]


def povoar():
    app = create_app()
    with app.app_context():
        db.create_all()

        if db.session.scalar(db.select(db.func.count(Usuario.id))):
            print("O banco ja contem dados. Nada foi alterado.")
            print("Para recomecar do zero, apague o arquivo portaria.db.")
            return

        unidades = {}
        for bloco, numero, descricao in UNIDADES:
            u = Unidade(bloco=bloco, numero=numero, descricao=descricao)
            db.session.add(u)
            unidades[(bloco, numero)] = u

        transportadoras = {}
        for nome in TRANSPORTADORAS:
            t = Transportadora(nome=nome)
            db.session.add(t)
            transportadoras[nome] = t

        usuarios = {}
        for nome, email, senha, perfil, chave_unidade in USUARIOS:
            usuario = Usuario(nome=nome, email=email, perfil=perfil)
            usuario.definir_senha(senha)
            if chave_unidade:
                usuario.unidade = unidades[chave_unidade]
            db.session.add(usuario)
            usuarios[email] = usuario

        db.session.flush()

        porteiro = usuarios["marcelino@portaria.local"]
        outro_porteiro = usuarios["enivaldo@portaria.local"]

        for codigo, bloco, numero, destinatario, transp, horas, retirou in ENCOMENDAS:
            recebida_em = agora() - timedelta(hours=horas)
            encomenda = Encomenda(
                codigo_rastreio=codigo,
                unidade=unidades[(bloco, numero)],
                destinatario=destinatario,
                transportadora=transportadoras[transp],
                situacao=SITUACAO_RECEBIDA,
                recebida_em=recebida_em,
                recebida_por=porteiro,
            )
            db.session.add(encomenda)
            db.session.flush()
            registrar_movimentacao(
                encomenda,
                MOV_RECEBIMENTO,
                usuario=porteiro,
                descricao=f"Recebida na portaria para a unidade {bloco} {numero}.",
            )
            encomenda.movimentacoes[-1].ocorrida_em = recebida_em

            if retirou:
                retirada_em = recebida_em + timedelta(hours=8)
                encomenda.situacao = SITUACAO_RETIRADA
                encomenda.retirada_em = retirada_em
                encomenda.retirada_por_nome = retirou
                encomenda.entregue_por = outro_porteiro
                registrar_movimentacao(
                    encomenda,
                    MOV_RETIRADA,
                    usuario=outro_porteiro,
                    descricao=f"Retirada por {retirou}.",
                )
                encomenda.movimentacoes[-1].ocorrida_em = retirada_em

        db.session.commit()

        print("Banco populado com sucesso.")
        print()
        print("  Porteiro : marcelino@portaria.local / portaria123")
        print("  Sindico  : sindico@portaria.local   / sindico123")
        print("  Morador  : ana@morador.local        / morador123")
        print()
        print("Inicie a aplicacao com: flask --app app:create_app run --debug")


if __name__ == "__main__":
    povoar()
