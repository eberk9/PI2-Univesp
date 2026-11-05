/* Painel do sindico (RF12): indicadores e as pendentes mais antigas. */
(function () {
  const aviso = document.getElementById('aviso-painel');
  const corpo = document.getElementById('corpo-antigas');
  if (!corpo) return;

  const MAIS_ANTIGAS = 5;

  function formatarTempo(horas) {
    if (horas === null || horas === undefined) return '—';
    if (horas < 24) return horas.toLocaleString('pt-BR') + ' h';
    const dias = Math.round((horas / 24) * 10) / 10;
    return dias.toLocaleString('pt-BR') + (dias === 1 ? ' dia' : ' dias');
  }

  function celula(texto) {
    const td = document.createElement('td');
    td.textContent = texto;
    return td;
  }

  async function carregar() {
    try {
      const [ind, lista] = await Promise.all([
        chamarApi('/indicadores'),
        chamarApi('/encomendas?situacao=RECEBIDA'),
      ]);
      if (!ind || !lista) return;

      document.getElementById('ind-pendentes').textContent = ind.pendentes;
      document.getElementById('ind-retiradas').textContent = ind.retiradas;
      document.getElementById('ind-devolvidas').textContent = ind.devolvidas;
      document.getElementById('ind-tempo').textContent =
        formatarTempo(ind.tempo_medio_retirada_horas);

      // A API devolve da mais recente para a mais antiga.
      const antigas = lista.encomendas.slice(-MAIS_ANTIGAS).reverse();
      corpo.textContent = '';
      if (antigas.length === 0) {
        const tr = document.createElement('tr');
        const td = celula('Nenhuma encomenda aguardando retirada.');
        td.colSpan = 4;
        td.className = 'vazio';
        tr.appendChild(td);
        corpo.appendChild(tr);
      }
      antigas.forEach((e) => {
        const tr = document.createElement('tr');
        const codigo = document.createElement('td');
        const link = document.createElement('a');
        link.href = '/encomendas/' + e.id;
        link.textContent = e.codigo_rastreio;
        codigo.appendChild(link);
        tr.append(
          codigo,
          celula(e.unidade ? e.unidade.identificacao : '—'),
          celula(e.destinatario),
          celula(formatarDataHora(e.recebida_em))
        );
        corpo.appendChild(tr);
      });
      aviso.textContent = 'Atualizado agora.';
    } catch (erro) {
      aviso.textContent = erro.message;
    }
  }

  carregar();
})();
