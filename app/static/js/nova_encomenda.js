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

/* Leitura do codigo de barras da etiqueta pela camera do celular.
   Usa o leitor nativo do navegador (BarcodeDetector); onde ele nao
   existe, como no Safari do iPhone, o botao continua oculto e o
   codigo e digitado. Le so codigos lineares: o Data Matrix dos
   Correios traz nome e endereco, nao o codigo de rastreio. */
(async function () {
  const botao = document.getElementById('ler-camera');
  const video = document.getElementById('video-camera');
  const campo = document.getElementById('codigo_rastreio');
  if (!botao || !('BarcodeDetector' in window)) return;

  const LINEARES = ['code_128', 'code_39', 'code_93', 'codabar', 'ean_13', 'itf'];
  const suportados = await BarcodeDetector.getSupportedFormats();
  const formatos = LINEARES.filter((f) => suportados.includes(f));
  if (formatos.length === 0) return;

  const leitor = new BarcodeDetector({ formats: formatos });
  let fluxo = null;

  function parar() {
    if (fluxo) fluxo.getTracks().forEach((t) => t.stop());
    fluxo = null;
    video.hidden = true;
    botao.textContent = 'Ler com a câmera';
  }

  async function procurar() {
    if (!fluxo) return;
    try {
      const achados = await leitor.detect(video);
      if (achados.length > 0) {
        campo.value = achados[0].rawValue.trim().toUpperCase();
        limparErro(campo);
        parar();
        document.getElementById('unidade_id').focus();
        return;
      }
    } catch (erro) {
      /* quadro ainda nao disponivel; tenta no proximo */
    }
    setTimeout(procurar, 250);
  }

  botao.addEventListener('click', async () => {
    if (fluxo) {
      parar();
      return;
    }
    limparErro(campo);
    try {
      fluxo = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
      });
    } catch (erro) {
      marcarErro(campo, 'Não foi possível abrir a câmera. Verifique a permissão do navegador ou digite o código.');
      return;
    }
    video.srcObject = fluxo;
    video.hidden = false;
    await video.play();
    botao.textContent = 'Parar câmera';
    procurar();
  });

  document.getElementById('form-encomenda').addEventListener('reset', parar);
  botao.hidden = false;
})();
