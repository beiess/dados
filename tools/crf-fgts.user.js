// ==UserScript==
// @name         CRF FGTS — automação (Caixa)
// @namespace    plenum.crf
// @version      1.0
// @description  Ao abrir a consulta da Caixa com um CNPJ no hash (#in=CNPJ), preenche, consulta, abre o Certificado, Visualiza e dispara a impressão (salvar PDF). NÃO burla CAPTCHA: se o desafio anti-robô aparecer, o script para e você resolve.
// @match        https://consulta-crf.caixa.gov.br/consultacrf/*
// @run-at       document-idle
// @grant        none
// ==/UserScript==
(function () {
  'use strict';
  var KEY = '__crf_auto';
  // 1) semear do hash (#in=CNPJ) na primeira chegada; guardar em sessionStorage (sobrevive aos POSTs do JSF)
  var m = (location.hash || '').match(/in=(\d{14})/);
  var st = null;
  try { st = JSON.parse(sessionStorage.getItem(KEY) || 'null'); } catch (e) {}
  if (m && (!st || st.cnpj !== m[1])) {
    st = { cnpj: m[1], step: 'consultar' };
    sessionStorage.setItem(KEY, JSON.stringify(st));
    history.replaceState(null, '', location.pathname + location.search); // limpa o hash
  }
  if (!st) return; // uso manual normal do site: não interferir

  function save() { sessionStorage.setItem(KEY, JSON.stringify(st)); }
  function done() { sessionStorage.removeItem(KEY); }
  function btn(t) {
    var all = document.querySelectorAll('input[type=button],input[type=submit],button');
    for (var i = 0; i < all.length; i++) { var v = (all[i].value || all[i].textContent || '').trim();
      if (v.toUpperCase().indexOf(t.toUpperCase()) >= 0) return all[i]; } return null; }
  function linkText(t) {
    var a = document.querySelectorAll('a');
    for (var i = 0; i < a.length; i++) if ((a[i].textContent || '').indexOf(t) >= 0) return a[i]; return null; }

  function run() {
    var html = document.body.innerHTML || '', body = document.body.innerText || '';
    // GUARDA CAPTCHA / bot-manager: parar e devolver o controle ao humano (NUNCA burlar)
    if (location.host.indexOf('perfdrive') >= 0 || /recaptcha|hcaptcha|g-recaptcha|sitekey|perfdrive/i.test(html)) {
      console.log('[CRF-auto] desafio anti-robô detectado — parando. Resolva manualmente e reinicie.');
      done(); return;
    }
    // passo 1: formulário → preencher Inscrição + Consultar
    var insc = document.querySelector('input[type=text]');
    if (st.step === 'consultar' && insc && btn('Consultar')) {
      insc.value = st.cnpj; insc.dispatchEvent(new Event('change', { bubbles: true }));
      st.step = 'cert'; save(); btn('Consultar').click(); return;
    }
    // passo 2: resultado → link do Certificado
    var cl = linkText('Certificado de Regularidade do FGTS');
    if (cl) { st.step = 'vis'; save(); cl.click(); return; }
    // passo 3: certificado → Visualizar
    var vb = btn('Visualizar');
    if (vb) { st.step = 'print'; save(); vb.click(); return; }
    // passo 4: página imprimível → imprimir (salvar PDF)
    if (/Certifica[çc][aã]o N[úu]mero/i.test(body) && btn('Imprimir')) {
      done(); setTimeout(function () { window.print(); }, 500); return;
    }
    // sem certificado / irregular
    if (/n[aã]o encontrad|situa[çc][aã]o irregular|n[aã]o.*regular/i.test(body) && st.step !== 'consultar') {
      done(); alert('[CRF-auto] CNPJ ' + st.cnpj + ': certificado indisponível (irregular ou não encontrado).'); return;
    }
  }
  setTimeout(run, 600); // dá tempo do JSF renderizar
})();
