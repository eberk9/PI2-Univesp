/* Tela de registro de encomenda. */
(function () {
  const form = document.getElementById('form-encomenda');
  const resultado = document.getElementById('resultado');
  if (!form) return;

  const obrigatorios = ['codigo_rastreio', 'unidade_id', 'destinatario'];

  obrigatorios.forEach((id) => {
    const campo = document.getElementById(id);
    campo.addEventListener('input', () => limparErro(campo));
    campo.addEventListener('change', () => limparErro(campo));
  });

  function validar() {
    let primeiroInvalido = null;
    obrigatorios.forEach((id) => {
      const campo = document.getElementById(id);
      if (!campo.value.trim()) {
        marcarErro(campo, 'Este campo é obrigatório.');
        if (!primeiroInvalido) primeiroInvalido = campo;
      }
    });
    if (primeiroInvalido) primeiroInvalido.focus();
    return primeiroInvalido === null;
  }

  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    resultado.textContent = '';
    if (!validar()) return;

    const botao = form.querySelector('button[type="submit"]');
    botao.disabled = true;
    botao.textContent = 'Registrando…';

    const dados = Object.fromEntries(new FormData(form).entries());

    try {
      const encomenda = await chamarApi('/encomendas', {
        method: 'POST',
        body: JSON.stringify(dados),
      });
      if (!encomenda) return;

      resultado.innerHTML =
        '<p class="aviso aviso--ok">Encomenda <strong>' +
        encomenda.codigo_rastreio +
        '</strong> registrada para a unidade ' +
        encomenda.unidade.identificacao +
        '. <a href="/encomendas/' + encomenda.id + '">Ver detalhes</a></p>';

      form.reset();
      document.getElementById('codigo_rastreio').focus();
    } catch (erro) {
      resultado.innerHTML = '<p class="aviso aviso--erro">' + erro.message + '</p>';
    } finally {
      botao.disabled = false;
      botao.textContent = 'Registrar encomenda';
    }
  });
})();
