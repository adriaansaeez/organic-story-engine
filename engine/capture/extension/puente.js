// Extension script on tiktok.com (isolated world). Receives what escucha.js reads, stores it in
// chrome.storage.local and, when the popup asks, opens Notifications > Followers and scrolls it.
/* global HSCenso */
(() => {
  // ------------------------------------------------------------ guardar (en cola para no pisarse)
  let cola = Promise.resolve();
  const guardar = (seguidores, meta) => {
    cola = cola.then(async () => {
      const prev = await chrome.storage.local.get(["seguidores", "meta"]);
      const { seguidores: todos, añadidos } = HSCenso.mezclar(prev.seguidores || {}, seguidores);
      await chrome.storage.local.set({
        seguidores: todos,
        meta: { ...(prev.meta || {}), ...(meta || {}), actualizado: Date.now(), ultimoLote: añadidos },
      });
    }).catch((e) => console.warn("[capture] not saved", e));
  };

  window.addEventListener("message", (e) => {
    if (e.source !== window || e.origin !== location.origin) return;
    const d = e.data;
    if (!d || d.__hsCenso !== 1 || typeof d.texto !== "string") return;
    let json;
    try { json = JSON.parse(d.texto); } catch { return; }
    const { seguidores, meta } = HSCenso.extraerNotificaciones(json);
    if (seguidores.length || meta) guardar(seguidores, meta);
  });

  // ------------------------------------------------------------ recoger (auto-scroll)
  const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
  const visible = (el) => el && el.getBoundingClientRect().height > 0;
  const panel = () => [...document.querySelectorAll('[class*="DivInboxContentContainer"]')].find(visible);
  const textoExacto = (re) =>
    [...document.querySelectorAll("button, [role='tab'], span, div, p")].find(
      (el) => el.childElementCount === 0 && re.test(el.textContent.trim()) && visible(el),
    );

  async function abrirPanel() {
    if (!panel()) {
      const boton = [...document.querySelectorAll("button, a, div[role='button']")].find((b) =>
        /bandeja de entrada|inbox|notificaciones|notifications/i.test(b.getAttribute("aria-label") || ""),
      );
      if (!boton) return false;
      boton.click();
      for (let i = 0; i < 20 && !panel(); i++) await dormir(250);
    }
    const filtro = textoExacto(/^(Seguidores|Followers)$/);
    if (filtro) { filtro.click(); await dormir(1500); }
    return !!panel();
  }

  let recogiendo = false;
  async function recoger() {
    if (recogiendo) return { ok: false, error: "Already collecting." };
    recogiendo = true;
    await chrome.storage.local.set({ recogiendo: true });
    try {
      if (!(await abrirPanel())) {
        return { ok: false, error: "Cannot find the notifications panel. Open it by hand (inbox icon) and choose Followers." };
      }
      const cuenta = async () => Object.keys((await chrome.storage.local.get("seguidores")).seguidores || {}).length;
      const inicio = await cuenta();
      let quietos = 0, prev = -1;
      for (let i = 0; i < 300 && quietos < 8; i++) {
        const p = panel();
        if (!p) break;
        p.scrollTop = p.scrollHeight - p.clientHeight - 300;
        await dormir(300);
        p.scrollTop = p.scrollHeight;
        await dormir(1500);
        await cola;
        const n = await cuenta();
        if (n === prev) quietos++; else { quietos = 0; prev = n; }
      }
      await cola;
      return { ok: true, nuevos: (await cuenta()) - inicio };
    } finally {
      recogiendo = false;
      await chrome.storage.local.set({ recogiendo: false });
    }
  }

  chrome.runtime.onMessage.addListener((msg, _sender, responder) => {
    if (msg && msg.tipo === "recoger") {
      recoger().then(responder, (e) => responder({ ok: false, error: String(e) }));
      return true; // respuesta asíncrona
    }
    if (msg && msg.tipo === "hola") responder({ ok: true });
  });
})();
