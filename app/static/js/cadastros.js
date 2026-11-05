/* Cadastros do sindico: unidades (RF02) e usuarios com perfil fixo (RF03).
   Usuarios nao sao excluidos, so desativados: o historico das encomendas
   continua apontando para quem registrou cada etapa. */
(function () {
  const formUnidade = document.getElementById('form-unidade');
  const formUsuario = document.getElementById('form-usuario');
  if (!formUnidade || !formUsuario) return;

  const corpoUnidades = document.getElementById('corpo-unidades');
  const corpoUsuarios = document.getElementById('corpo-usuarios');
  const seletorUnidade = document.getElementById('unidade_id');
  const seletorPerfil = document.getElementById('perfil');
  const campoUnidade = document.getElementById('campo-unidade-usuario');
  const resultadoUnidade = document.getElementById('resultado-unidade');
  const resultadoUsuario = document.getElementById('resultado-usuario');

  function celula(texto) {
    const td = document.createElement('td');
    td.textContent = texto;
    return td;
  }

  function botao(texto, rotuloAcessivel) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'botao botao--secundario';
    b.textContent = texto;
    b.setAttribute('aria-label', rotuloAcessivel);
    return b;
  }

  function avisar(alvo, mensagem, tipo) {
    alvo.textContent = '';
    const p = document.createElement('p');
    p.className = 'aviso aviso--' + tipo;
    p.textContent = mensagem;
    alvo.appendChild(p);
  }

  function validar(ids) {
    let primeiro = null;
    ids.forEach((id) => {
      const campo = document.getElementById(id);
      limparErro(campo);
      if (!campo.value.trim()) {
        marcarErro(campo, 'Este campo é obrigatório.');
        if (!primeiro) primeiro = campo;
      }
    });
    if (primeiro) primeiro.focus();
    return primeiro === null;
  }

  /* ---------------------------------------------------------- unidades */
  async function carregarUnidades() {
    const dados = await chamarApi('/unidades');
    if (!dados) return;
    corpoUnidades.textContent = '';
    seletorUnidade.length = 1;
    dados.unidades.forEach((u) => {
      const tr = document.createElement('tr');
      tr.append(celula(u.identificacao), celula(u.descricao || '—'));
      corpoUnidades.appendChild(tr);
      seletorUnidade.add(new Option(u.identificacao, u.id));
    });
  }

  formUnidade.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    resultadoUnidade.textContent = '';
    if (!validar(['numero'])) return;
    try {
      const unidade = await chamarApi('/unidades', {
        method: 'POST',
        body: JSON.stringify(Object.fromEntries(new FormData(formUnidade).entries())),
      });
      if (!unidade) return;
      avisar(resultadoUnidade, 'Unidade ' + unidade.identificacao + ' cadastrada.', 'ok');
      formUnidade.reset();
      await carregarUnidades();
      document.getElementById('bloco').focus();
    } catch (erro) {
      avisar(resultadoUnidade, erro.message, 'erro');
    }
  });

  /* ---------------------------------------------------------- usuarios */
  function ajustarUnidade() {
    const morador = seletorPerfil.value === 'MORADOR';
    campoUnidade.hidden = !morador;
    seletorUnidade.required = morador;
    if (!morador) limparErro(seletorUnidade);
  }
  seletorPerfil.addEventListener('change', ajustarUnidade);

  /* Formulario embutido na linha, como a baixa na tela de encomendas. */
  function abrirSenha(usuario, linha, botaoSenha) {
    if (linha.nextElementSibling && linha.nextElementSibling.dataset.senha) return;
    botaoSenha.disabled = true;

    const tr = document.createElement('tr');
    tr.dataset.senha = String(usuario.id);
    const td = document.createElement('td');
    td.colSpan = 6;
    const form = document.createElement('form');
    form.className = 'campo campo--baixa';

    const id = 'nova-senha-' + usuario.id;
    const rotulo = document.createElement('label');
    rotulo.htmlFor = id;
    rotulo.textContent = 'Nova senha de ' + usuario.nome + ' (mínimo de 8 caracteres)';
    const entrada = document.createElement('input');
    entrada.type = 'password';
    entrada.id = id;
    entrada.autocomplete = 'new-password';
    const confirmar = document.createElement('button');
    confirmar.type = 'submit';
    confirmar.className = 'botao botao--primario';
    confirmar.textContent = 'Salvar senha';
    const cancelar = botao('Cancelar', 'Cancelar');

    function fechar() {
      tr.remove();
      botaoSenha.disabled = false;
      botaoSenha.focus();
    }
    cancelar.addEventListener('click', fechar);
    entrada.addEventListener('keydown', (e) => { if (e.key === 'Escape') fechar(); });
    entrada.addEventListener('input', () => limparErro(entrada));
    form.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      try {
        await chamarApi('/usuarios/' + usuario.id, {
          method: 'PATCH',
          body: JSON.stringify({ senha: entrada.value }),
        });
        fechar();
        avisar(resultadoUsuario, 'Senha de ' + usuario.nome + ' redefinida.', 'ok');
      } catch (erro) {
        marcarErro(entrada, erro.message);
      }
    });

    form.append(rotulo, entrada, confirmar, cancelar);
    td.appendChild(form);
    tr.appendChild(td);
    linha.insertAdjacentElement('afterend', tr);
    entrada.focus();
  }

  async function alternarAtivo(usuario) {
    try {
      await chamarApi('/usuarios/' + usuario.id, {
        method: 'PATCH',
        body: JSON.stringify({ ativo: !usuario.ativo }),
      });
      avisar(resultadoUsuario, usuario.nome + (usuario.ativo ? ' desativado.' : ' reativado.'), 'ok');
      await carregarUsuarios();
    } catch (erro) {
      avisar(resultadoUsuario, erro.message, 'erro');
    }
  }

  async function carregarUsuarios() {
    const dados = await chamarApi('/usuarios');
    if (!dados) return;
    corpoUsuarios.textContent = '';
    dados.usuarios.forEach((u) => {
      const tr = document.createElement('tr');

      const situacao = document.createElement('td');
      const etiqueta = document.createElement('span');
      etiqueta.className = 'etiqueta ' + (u.ativo ? 'etiqueta--retirada' : 'etiqueta--devolvida');
      etiqueta.textContent = u.ativo ? 'ativo' : 'inativo';
      situacao.appendChild(etiqueta);

      const acoes = document.createElement('td');
      acoes.className = 'acoes';
      const textoAtivo = u.ativo ? 'Desativar' : 'Reativar';
      const ativar = botao(textoAtivo, textoAtivo + ' ' + u.nome);
      ativar.addEventListener('click', () => alternarAtivo(u));
      const senha = botao('Redefinir senha', 'Redefinir senha de ' + u.nome);
      senha.addEventListener('click', () => abrirSenha(u, tr, senha));
      acoes.append(ativar, senha);

      tr.append(
        celula(u.nome),
        celula(u.email),
        celula(NOMES_PERFIL[u.perfil] || u.perfil),
        celula(u.unidade || '—'),
        situacao,
        acoes
      );
      corpoUsuarios.appendChild(tr);
    });
  }

  formUsuario.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    resultadoUsuario.textContent = '';
    const obrigatorios = ['nome', 'email', 'senha'];
    if (seletorPerfil.value === 'MORADOR') obrigatorios.push('unidade_id');
    if (!validar(obrigatorios)) return;

    const dados = Object.fromEntries(new FormData(formUsuario).entries());
    dados.unidade_id = dados.unidade_id ? Number(dados.unidade_id) : null;
    try {
      const usuario = await chamarApi('/usuarios', { method: 'POST', body: JSON.stringify(dados) });
      if (!usuario) return;
      avisar(resultadoUsuario, 'Usuário ' + usuario.nome + ' cadastrado como ' +
        (NOMES_PERFIL[usuario.perfil] || usuario.perfil).toLowerCase() + '.', 'ok');
      formUsuario.reset();
      ajustarUnidade();
      await carregarUsuarios();
      document.getElementById('nome').focus();
    } catch (erro) {
      avisar(resultadoUsuario, erro.message, 'erro');
    }
  });

  ajustarUnidade();
  carregarUnidades().catch((e) => avisar(resultadoUnidade, e.message, 'erro'));
  carregarUsuarios().catch((e) => avisar(resultadoUsuario, e.message, 'erro'));
})();
