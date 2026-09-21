/* Lista de encomendas com busca assincrona e baixa na retirada.
   A baixa usa um formulario embutido na propria linha, e nao um dialogo
   do navegador: e mais acessivel e nao bloqueia a pagina. */
(function () {
  const corpo = document.getElementById('corpo-tabela');
  const contador = document.getElementById('contador');
  const campoBusca = document.getElementById('q');
  const campoSituacao = document.getElementById('situacao');
  if (!corpo) return;

  const COLUNAS = 6;

  async function carregar() {
    const parametros = new URLSearchParams();
    if (campoBusca.value.trim()) parametros.set('q', campoBusca.value.trim());
    if (campoSituacao.value) parametros.set('situacao', campoSituacao.value);

    try {
      const dados = await chamarApi('/encomendas?' + parametros.toString());
      if (!dados) return;
      desenhar(dados.encomendas);
      contador.textContent =
        dados.total === 0
          ? 'Nenhuma encomenda encontrada.'
          : dados.total + (dados.total === 1 ? ' encomenda' : ' encomendas');
    } catch (erro) {
      contador.textContent = erro.message;
    }
  }

  function linhaVazia(mensagem) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = COLUNAS;
    td.className = 'vazio';
    td.textContent = mensagem;
    tr.appendChild(td);
    return tr;
  }

  function desenhar(encomendas) {
    corpo.textContent = '';

    if (encomendas.length === 0) {
      corpo.appendChild(linhaVazia('Nenhuma encomenda encontrada.'));
      return;
    }

    encomendas.forEach((e) => {
      const tr = document.createElement('tr');

      const codigo = document.createElement('td');
      const link = document.createElement('a');
      link.href = '/encomendas/' + e.id;
      link.textContent = e.codigo_rastreio;
      codigo.appendChild(link);

      const unidade = document.createElement('td');
      unidade.textContent = e.unidade ? e.unidade.identificacao : '—';

      const destinatario = document.createElement('td');
      destinatario.textContent = e.destinatario;

      const recebida = document.createElement('td');
      recebida.textContent = formatarDataHora(e.recebida_em);

      const situacao = document.createElement('td');
      situacao.appendChild(etiquetaSituacao(e.situacao));

      const acoes = document.createElement('td');
      if (e.situacao === 'RECEBIDA') {
        const botao = document.createElement('button');
        botao.type = 'button';
        botao.className = 'botao botao--secundario';
        botao.textContent = 'Dar baixa';
        botao.setAttribute(
          'aria-label',
          'Dar baixa na encomenda ' + e.codigo_rastreio
        );
        botao.addEventListener('click', () => abrirBaixa(e, tr, botao));
        acoes.appendChild(botao);
      } else {
        acoes.textContent = e.retirada_por_nome || '—';
      }

      [codigo, unidade, destinatario, recebida, situacao, acoes].forEach((td) =>
        tr.appendChild(td)
      );
      corpo.appendChild(tr);
    });
  }

  /* Abre, logo abaixo da linha, o campo "quem retirou". */
  function abrirBaixa(encomenda, linha, botao) {
    if (linha.nextElementSibling &&
        linha.nextElementSibling.dataset.baixa === String(encomenda.id)) {
      return;
    }

    botao.disabled = true;

    const tr = document.createElement('tr');
    tr.dataset.baixa = String(encomenda.id);

    const td = document.createElement('td');
    td.colSpan = COLUNAS;

    const form = document.createElement('form');
    form.className = 'campo campo--baixa';

    const idCampo = 'quem-retirou-' + encomenda.id;
    const rotulo = document.createElement('label');
    rotulo.htmlFor = idCampo;
    rotulo.textContent =
      'Quem está retirando a encomenda ' + encomenda.codigo_rastreio + '?';

    const entrada = document.createElement('input');
    entrada.type = 'text';
    entrada.id = idCampo;
    entrada.required = true;
    entrada.autocomplete = 'off';

    const confirmar = document.createElement('button');
    confirmar.type = 'submit';
    confirmar.className = 'botao botao--primario';
    confirmar.textContent = 'Confirmar retirada';

    const cancelar = document.createElement('button');
    cancelar.type = 'button';
    cancelar.className = 'botao botao--secundario';
    cancelar.textContent = 'Cancelar';

    function fechar() {
      tr.remove();
      botao.disabled = false;
      botao.focus();
    }

    cancelar.addEventListener('click', fechar);
    entrada.addEventListener('keydown', (ev) => {
      if (ev.key === 'Escape') fechar();
    });
    entrada.addEventListener('input', () => limparErro(entrada));

    form.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const nome = entrada.value.trim();
      if (!nome) {
        marcarErro(entrada, 'Informe o nome de quem está retirando.');
        entrada.focus();
        return;
      }

      confirmar.disabled = true;
      confirmar.textContent = 'Confirmando…';
      try {
        await chamarApi('/encomendas/' + encomenda.id + '/retirada', {
          method: 'POST',
          body: JSON.stringify({ retirada_por_nome: nome }),
        });
        contador.textContent =
          'Baixa registrada: ' + encomenda.codigo_rastreio + ' retirada por ' + nome + '.';
        await carregar();
      } catch (erro) {
        marcarErro(entrada, erro.message);
        confirmar.disabled = false;
        confirmar.textContent = 'Confirmar retirada';
      }
    });

    form.append(rotulo, entrada, confirmar, cancelar);
    td.appendChild(form);
    tr.appendChild(td);
    linha.insertAdjacentElement('afterend', tr);
    entrada.focus();
  }

  campoBusca.addEventListener('input', aguardar(carregar, 300));
  campoSituacao.addEventListener('change', carregar);
  document.getElementById('form-busca').addEventListener('submit', (ev) => {
    ev.preventDefault();
    carregar();
  });

  carregar();
})();
