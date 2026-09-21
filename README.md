# Sistema Web de Controle de Encomendas para Portarias

Projeto Integrador em Computação II — UNIVESP, Polo Piracicaba, 2026 — Grupo 6.

Aplicação web para registrar o ciclo de vida das encomendas recebidas na portaria
de um residencial: quem recebeu, quando, quem retirou e quem entregou. Campo de
pesquisa: portaria do Residencial Terras de Ártemis, Artemis, Piracicaba/SP.

## Como rodar localmente

Pré-requisito: Python 3.11 ou superior. Não é preciso instalar MySQL para
desenvolver — o banco padrão é um arquivo SQLite local.

```bash
git clone <url-do-repositorio>
cd encomendas-portaria

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # opcional em desenvolvimento

python seed.py                # cria as tabelas e popula dados de demonstração
flask --app app:create_app run --debug
```

Abra <http://localhost:5000>.

### Usuários de demonstração

| Perfil   | E-mail                     | Senha       |
|----------|----------------------------|-------------|
| Porteiro | marcelino@portaria.local   | portaria123 |
| Síndico  | sindico@portaria.local     | sindico123  |
| Morador  | ana@morador.local          | morador123  |

Todos os dados do `seed.py` são fictícios. **Dados reais de moradores nunca entram
no repositório** — ver RNF04 (minimização, LGPD) no Relatório Parcial.

## Testes

```bash
pytest -q
```

Os testes cobrem autenticação, controle de acesso por perfil, registro de
encomenda, baixa na retirada, integridade do histórico e os filtros de busca.
Rodam também no GitHub Actions a cada push e pull request.

## Estrutura

```
app/
  __init__.py        fábrica da aplicação
  extensions.py      db, login_manager, migrate
  models.py          as 5 entidades (Apêndice A do Relatório Parcial)
  auth.py            login e logout por sessão
  main.py            rotas das páginas HTML
  api/               API REST sob /api/v1
  templates/         HTML semântico
  static/css/        estilos, com contraste verificado para WCAG AA
  static/js/         scripts que consomem a API
tests/               pytest
config.py            configuração por variáveis de ambiente
seed.py              dados de demonstração
```

## A API

Todas as páginas leem e gravam pela API — nenhuma consulta o banco direto.

| Método | Recurso | Perfis |
|---|---|---|
| POST | `/api/v1/sessoes` | público |
| DELETE | `/api/v1/sessoes` | autenticado |
| GET | `/api/v1/encomendas` | todos (morador vê só a sua unidade) |
| POST | `/api/v1/encomendas` | porteiro, síndico |
| GET | `/api/v1/encomendas/{id}` | todos |
| POST | `/api/v1/encomendas/{id}/retirada` | porteiro, síndico |
| POST | `/api/v1/encomendas/{id}/devolucao` | porteiro, síndico |
| GET | `/api/v1/unidades` | autenticado |
| GET | `/api/v1/transportadoras` | autenticado |
| GET | `/api/v1/indicadores` | porteiro, síndico |

Filtros de `GET /encomendas`: `?situacao=&unidade=&de=&ate=&q=`.

## Implantação em nuvem (PythonAnywhere)

1. Criar conta gratuita e enviar o código (`git clone` no console do Bash).
2. Criar o banco MySQL na aba **Databases**.
3. Na aba **Web**, criar uma app manual com Python 3.12 e apontar o virtualenv.
4. No arquivo WSGI:
   ```python
   import sys, os
   sys.path.insert(0, '/home/USUARIO/encomendas-portaria')
   os.environ['SECRET_KEY'] = '...'
   os.environ['DATABASE_URL'] = 'mysql+pymysql://USUARIO:SENHA@USUARIO.mysql.pythonanywhere-services.com/USUARIO$portaria'
   from app import create_app
   application = create_app()
   ```
5. Rodar `python seed.py` uma vez no console, com as mesmas variáveis de ambiente.

`SECRET_KEY` e `DATABASE_URL` nunca vão para o repositório.

## Como trabalhamos

- Uma branch por funcionalidade: `feat/registro-encomenda`, `fix/busca-acentos`.
- Ninguém envia código direto para a `main` — sempre por pull request.
- Todo PR precisa da revisão de outro integrante e do CI verde.

## Equipe

Anderson Alexandre Robles · Beatriz Fernanda Alves Fuentes · Eber Constantinov ·
Eduardo Lopes · Isac Matheus de Carvalho Lopes · Pedro Donizete da Costa Filho ·
Renan Polesi

Orientadora: Milena Rosa de Souza.
