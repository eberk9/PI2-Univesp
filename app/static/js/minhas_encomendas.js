/* Tela do morador: somente leitura das encomendas da propria unidade. */
(function () {
  const corpo = document.getElementById('corpo-tabela');
  const contador = document.getElementById('contador');
  if (!corpo) return;

  async function carregar() {
    try {
      const dados = await chamarApi('/encomendas');
      if (!dados) return;

      corpo.textContent = '';

      if (dados.total === 0) {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 4;
        td.className = 'vazio';
        td.textContent = 'Nenhuma encomenda registrada para a sua unidade.';
        tr.appendChild(td);
        corpo.appendChild(tr);
      } else {
        dados.encomendas.forEach((e) => {
          const tr = document.createElement('tr');

          const codigo = document.createElement('td');
          const link = document.createElement('a');
          link.href = '/encomendas/' + e.id;
          link.textContent = e.codigo_rastreio;
          codigo.appendChild(link);

          const destinatario = document.createElement('td');
          destinatario.textContent = e.destinatario;

          const recebida = document.createElement('td');
          recebida.textContent = formatarDataHora(e.recebida_em);

          const situacao = document.createElement('td');
          situacao.appendChild(etiquetaSituacao(e.situacao));

          [codigo, destinatario, recebida, situacao].forEach((td) =>
            tr.appendChild(td)
          );
          corpo.appendChild(tr);
        });
      }

      const pendentes = dados.encomendas.filter(
        (e) => e.situacao === 'RECEBIDA'
      ).length;
      contador.textContent =
        pendentes === 0
          ? 'Nenhuma encomenda aguardando retirada.'
          : pendentes +
            (pendentes === 1
              ? ' encomenda aguardando retirada.'
              : ' encomendas aguardando retirada.');
    } catch (erro) {
      contador.textContent = erro.message;
    }
  }

  carregar();
})();
