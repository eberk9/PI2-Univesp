/* Funcoes compartilhadas pelas telas. Toda a leitura e escrita de dados
   passa pela API REST em /api/v1 -- nenhuma pagina consulta o banco direto. */

const API = '/api/v1';

async function chamarApi(caminho, opcoes = {}) {
  const resposta = await fetch(API + caminho, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    ...opcoes,
  });

  if (resposta.status === 401) {
    window.location.href = '/login';
    return null;
  }

  let corpo = null;
  if (resposta.status !== 204) {
    corpo = await resposta.json().catch(() => null);
  }

  if (!resposta.ok) {
    const mensagem = (corpo && corpo.erro) || 'Nao foi possivel completar a operacao.';
    throw new Error(mensagem);
  }
  return corpo;
}

function formatarDataHora(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function etiquetaSituacao(situacao) {
  const span = document.createElement('span');
  span.className = 'etiqueta etiqueta--' + situacao.toLowerCase();
  span.textContent = situacao.toLowerCase();
  return span;
}

/* Executa a funcao so depois que o usuario parar de digitar. */
function aguardar(fn, ms = 300) {
  let id;
  return (...args) => {
    clearTimeout(id);
    id = setTimeout(() => fn(...args), ms);
  };
}

/* Mensagem de erro associada ao campo via aria-describedby, para que
   leitores de tela a anunciem (criterio 3.3.1 da WCAG). */
function marcarErro(campo, mensagem) {
  limparErro(campo);
  campo.setAttribute('aria-invalid', 'true');
  const aviso = document.createElement('span');
  aviso.className = 'erro-campo';
  aviso.id = 'erro-' + campo.id;
  aviso.textContent = mensagem;
  campo.insertAdjacentElement('afterend', aviso);
  campo.setAttribute('aria-describedby', aviso.id);
}

function limparErro(campo) {
  campo.removeAttribute('aria-invalid');
  const existente = document.getElementById('erro-' + campo.id);
  if (existente) existente.remove();
}
