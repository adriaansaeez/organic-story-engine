// Captures every comment of one TikTok video (read-only).
// Evaluate it INSIDE the video page (e.g. the agent's built-in browser javascript tool), prefixed with
// `await `, right after loading https://www.tiktok.com/@<account>/video/<id> with the comments panel
// CLOSED, so it hears the first page too.
//
// It only LISTENS to the /api/comment/list/ (and /reply/) responses the page itself requests, opens the
// panel, scrolls it to the end and expands replies. It never likes, replies or writes anything.
//
// Returns { video, url, titulo, total, capturados, comentarios: [{cid, usuario, nombre, texto, ts, likes, respuesta_a}] }
// oldest first (ts = exact comment time, seconds). Field names are in Spanish;
// `engine/audience/audience.py requests` reads them as handle/name/text.
(async () => {
  const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
  const visible = (e) => e && e.getBoundingClientRect().height > 0;
  const video = (location.pathname.match(/\/video\/(\d+)/) || [])[1] || null;
  const porCid = new Map();

  const leer = (texto) => {
    let j; try { j = JSON.parse(texto); } catch { return; }
    for (const c of (j && j.comments) || []) {
      const u = c.user || {};
      if (!c.cid || !u.unique_id) continue;
      porCid.set(String(c.cid), {
        cid: String(c.cid),
        usuario: String(u.unique_id).toLowerCase(),
        nombre: u.nickname || null,
        texto: c.text || "",
        ts: Number(c.create_time) || null,
        likes: Number(c.digg_count) || 0,
        respuesta_a: c.reply_id && String(c.reply_id) !== "0" ? String(c.reply_id) : null,
      });
    }
  };

  // escucha pasiva (no toca peticiones ni respuestas)
  const RUTA = /\/api\/comment\/list\//;
  if (!window.__hsComentarios) {
    window.__hsComentarios = [];
    const f0 = window.fetch;
    window.fetch = function (...a) {
      const p = f0.apply(this, a);
      try {
        const url = typeof a[0] === "string" ? a[0] : a[0] && a[0].url;
        if (url && RUTA.test(url)) p.then((r) => r.clone().text().then((t) => window.__hsComentarios.push(t))).catch(() => {});
      } catch {}
      return p;
    };
    const abrir = XMLHttpRequest.prototype.open, enviar = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function (m, url, ...r) { this.__hsUrl = url; return abrir.call(this, m, url, ...r); };
    XMLHttpRequest.prototype.send = function (...a) {
      if (this.__hsUrl && RUTA.test(String(this.__hsUrl))) {
        this.addEventListener("load", () => { try { window.__hsComentarios.push(this.responseText); } catch {} });
      }
      return enviar.apply(this, a);
    };
  }

  // abrir el panel de comentarios del vídeo visible
  const items = () => document.querySelectorAll('[class*="DivCommentObjectWrapper"]').length;
  if (!items()) {
    const icono = [...document.querySelectorAll('[data-e2e="comment-icon"]')].find((e) => {
      const r = e.getBoundingClientRect();
      return r.height > 0 && r.top >= 0 && r.top < innerHeight;
    }) || document.querySelector('[data-e2e="comment-icon"]');
    if (icono) icono.click();
    for (let i = 0; i < 20 && !items(); i++) await dormir(400);
  }
  if (!items()) return { error: "No se abre el panel de comentarios (¿vídeo sin comentarios o ventana muy pequeña?)", video };

  // bajar hasta el final
  let caja = document.querySelector('[class*="DivCommentListContainer"]');
  while (caja && caja.scrollHeight <= caja.clientHeight + 5) caja = caja.parentElement;
  let prev = -1, quietos = 0;
  for (let i = 0; i < 120 && quietos < 4; i++) {
    if (caja) caja.scrollTop = caja.scrollHeight;
    await dormir(1200);
    const n = items();
    if (n === prev) quietos++; else { quietos = 0; prev = n; }
  }

  // desplegar respuestas ("Ver N respuestas", "Ver más")
  for (let r = 0; r < 15; r++) {
    const botones = [...document.querySelectorAll("span, p, div")].filter(
      (e) => e.childElementCount === 0 && visible(e) && /^(Ver \d+ respuestas?|Ver más|View \d+ repl|View more)/i.test(e.textContent.trim()),
    );
    if (!botones.length) break;
    for (const b of botones) { b.click(); await dormir(900); }
  }
  await dormir(1500);

  for (const t of window.__hsComentarios) leer(t);

  // red de seguridad: lo que se ve en pantalla y no llegó por la API (sin hora)
  let sinHora = 0;
  for (const it of document.querySelectorAll('[class*="DivCommentItemWrapper"]')) {
    const a = it.querySelector('[data-e2e^="comment-username"] a');
    const texto = ((it.querySelector('[data-e2e^="comment-level"]') || {}).textContent || "").trim();
    if (!a || !texto) continue;
    const usuario = a.getAttribute("href").replace(/^\/@/, "").split(/[/?]/)[0].toLowerCase();
    const ya = [...porCid.values()].some((c) => c.usuario === usuario && c.texto.trim() === texto);
    if (!ya) {
      sinHora++;
      porCid.set(`dom-${sinHora}`, { cid: null, usuario, nombre: null, texto, ts: null,
        likes: Number(((it.querySelector('[class*="DivLikeContainer"]') || {}).textContent || "0").trim()) || 0, respuesta_a: null });
    }
  }

  const total = Number(((document.querySelector('[data-e2e="comment-icon"]') || {}).getAttribute?.("aria-label") || "").match(/(\d+)\s*comentarios/)?.[1]) || null;
  const comentarios = [...porCid.values()].sort((a, b) => (a.ts ?? Infinity) - (b.ts ?? Infinity));
  const titulo = document.title.replace(/\s*\|\s*TikTok\s*$/, "").trim() || null;
  return { video, url: video ? `${location.origin}${(location.pathname.match(/^\/@[^/]+/) || [""])[0]}/video/${video}` : location.href, titulo, total,
    capturados: comentarios.length, sin_hora: sinHora, comentarios };
})();
