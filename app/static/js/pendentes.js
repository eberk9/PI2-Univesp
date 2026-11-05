/* Lista de encomendas com busca assincrona, baixa na retirada e devolucao.
   A baixa usa um formulario embutido na propria linha, e nao um dialogo
   do navegador: e mais acessivel e nao bloqueia a pagina. */
(function () {
  const corpo = document.getElementById('corpo-tabela');
  const contador = document.getElementById('contador');
  const campoBusca = document.getElementById('q');
  const campoSituacao = document.getElementById('situacao');
  const campoDe = document.getElementById('de');
  const campoAte = document.getElementById('ate');
  const colRetirada = document.getElementById('col-retirada');
  if (!corpo) return;

  let COLUNAS = 6;

  async function carregar() {
    const parametros = new URLSearchParams();
    if (campoBusca.value.trim()) parametros.set('q', campoBusca.value.trim());
    if (campoSituacao.value) parametros.set('situacao', campoSituacao.value);
    if (campoDe.value) parametros.set('de', campoDe.value);
    if (campoAte.value) parametros.set('ate', campoAte.value);

    // A coluna "Retirada em" so faz sentido fora da lista de pendentes.
    colRetirada.hidden = campoSituacao.value === 'RECEBIDA';
    COLUNAS = colRetirada.hidden ? 6 : 7;

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
        const botoes = [BAIXA, DEVOLUCAO].map((acao) => {
          const botao = document.createElement('button');
          botao.type = 'button';
          botao.className = 'botao botao--secundario';
          botao.textContent = acao.botao;
          botao.setAttribute('aria-label', acao.botao + ' na encomenda ' + e.codigo_rastreio);
          return botao;
        });
        botoes[0].addEventListener('click', () => abrirAcao(BAIXA, e, tr, botoes));
        botoes[1].addEventListener('click', () => abrirAcao(DEVOLUCAO, e, tr, botoes));
        acoes.className = 'acoes';
        acoes.append(...botoes);
      } else {
        acoes.textContent = e.retirada_por_nome || '—';
      }

      const colunas = [codigo, unidade, destinatario, recebida];
      if (!colRetirada.hidden) {
        const retirada = document.createElement('td');
        retirada.textContent = e.retirada_em ? formatarDataHora(e.retirada_em) : '—';
        colunas.push(retirada);
      }
      colunas.push(situacao, acoes);
      colunas.forEach((td) => tr.appendChild(td));
      corpo.appendChild(tr);
    });
  }

  /* Baixa (RF08) e devolucao (RF09) usam o mesmo formulario embutido. */
  const BAIXA = {
    botao: 'Dar baixa',
    pergunta: (codigo) => 'Quem está retirando a encomenda ' + codigo + '?',
    obrigatorio: 'Informe o nome de quem está retirando.',
    confirmar: 'Confirmar retirada',
    rota: '/retirada',
    campo: 'retirada_por_nome',
    aviso: (codigo, valor) => 'Baixa registrada: ' + codigo + ' retirada por ' + valor + '.',
  };
  const DEVOLUCAO = {
    botao: 'Devolver',
    pergunta: (codigo) =>
      'Motivo da devolução da encomenda ' + codigo + ' à transportadora (opcional)',
    obrigatorio: null,
    confirmar: 'Confirmar devolução',
    rota: '/devolucao',
    campo: 'motivo',
    aviso: (codigo) => 'Devolução registrada: ' + codigo + '.',
  };

  /* Abre, logo abaixo da linha, o campo da acao escolhida. */
  function abrirAcao(acao, encomenda, linha, botoes) {
    if (linha.nextElementSibling &&
        linha.nextElementSibling.dataset.acao === String(encomenda.id)) {
      return;
    }

    botoes.forEach((b) => { b.disabled = true; });

    const tr = document.createElement('tr');
    tr.dataset.acao = String(encomenda.id);

    const td = document.createElement('td');
    td.colSpan = COLUNAS;

    const form = document.createElement('form');
    form.className = 'campo campo--baixa';

    const idCampo = 'acao-' + encomenda.id;
    const rotulo = document.createElement('label');
    rotulo.htmlFor = idCampo;
    rotulo.textContent = acao.pergunta(encomenda.codigo_rastreio);

    const entrada = document.createElement('input');
    entrada.type = 'text';
    entrada.id = idCampo;
    entrada.required = Boolean(acao.obrigatorio);
    entrada.autocomplete = 'off';

    const confirmar = document.createElement('button');
    confirmar.type = 'submit';
    confirmar.className = 'botao botao--primario';
    confirmar.textContent = acao.confirmar;

    const cancelar = document.createElement('button');
    cancelar.type = 'button';
    cancelar.className = 'botao botao--secundario';
    cancelar.textContent = 'Cancelar';

    function fechar() {
      tr.remove();
      botoes.forEach((b) => { b.disabled = false; });
      botoes[0].focus();
    }

    cancelar.addEventListener('click', fechar);
    entrada.addEventListener('keydown', (ev) => {
      if (ev.key === 'Escape') fechar();
    });
    entrada.addEventListener('input', () => limparErro(entrada));

    form.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const valor = entrada.value.trim();
      if (!valor && acao.obrigatorio) {
        marcarErro(entrada, acao.obrigatorio);
        entrada.focus();
        return;
      }

      confirmar.disabled = true;
      confirmar.textContent = 'Confirmando…';
      const corpoJson = {};
      if (valor) corpoJson[acao.campo] = valor;
      try {
        await chamarApi('/encomendas/' + encomenda.id + acao.rota, {
          method: 'POST',
          body: JSON.stringify(corpoJson),
        });
        // Recarrega antes de avisar: carregar() reescreve o contador.
        await carregar();
        contador.textContent = acao.aviso(encomenda.codigo_rastreio, valor);
      } catch (erro) {
        marcarErro(entrada, erro.message);
        confirmar.disabled = false;
        confirmar.textContent = acao.confirmar;
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
  campoDe.addEventListener('change', carregar);
  campoAte.addEventListener('change', carregar);
  document.getElementById('form-busca').addEventListener('submit', (ev) => {
    ev.preventDefault();
    carregar();
  });

  carregar();
})();
