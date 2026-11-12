// Collects new followers from TikTok's notifications panel (the "Followers" filter).
// Evaluate it INSIDE tiktok.com with the panel open and filtered to Followers. First set
// window.__censo = [handles already in the census] (audience.py roster --json gives them).
//
// Scrolls until it meets someone already in the census (the "stop") or TikTok stops loading.
// Returns the new ones OLDEST first, ready to import. If it never reaches the stop there is a
// gap: older followers the web no longer shows (use the official data export, see ose-census).
(async () => {
  const conocidos = new Set((window.__censo || []).map((u) => String(u).toLowerCase()));
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const visible = (e) => e.getBoundingClientRect().height > 0;
  const cont = [...document.querySelectorAll('[class*="DivInboxContentContainer"]')].find(visible);
  if (!cont) return { error: "No veo el panel de notificaciones abierto. Abre Notificaciones y elige 'Seguidores'." };

  const orden = [], vistos = new Set();
  const usuarioDe = (a) => a.getAttribute("href").slice(2).split(/[/?]/)[0].toLowerCase();
  let tope = null;
  const recoger = () => {
    for (const li of cont.querySelectorAll("li")) {
      const a = li.querySelector('a[href^="/@"]');
      if (!a) continue;
      const u = usuarioDe(a);
      if (!u || vistos.has(u)) continue;
      vistos.add(u);
      if (conocidos.has(u)) { if (!tope) tope = u; continue; }
      orden.push(u); // TikTok lista del más reciente al más antiguo
    }
  };

  let quietos = 0, prev = -1;
  for (let i = 0; i < 400 && quietos < 6; i++) {
    recoger();
    // tras el tope, unas cuantas filas más por si alguien re-siguió, y paramos
    if (tope && vistos.size - orden.length > 15) break;
    cont.scrollTop = cont.scrollHeight - cont.clientHeight - 300;
    await sleep(300);
    cont.scrollTop = cont.scrollHeight;
    await sleep(1600);
    recoger();
    if (vistos.size === prev) quietos++; else { quietos = 0; prev = vistos.size; }
  }

  // los que aparecen ANTES del tope son nuevos; los de después del tope, si no estaban, son raros (re-seguidores)
  return {
    nuevos: orden.slice().reverse(),
    tope,
    hueco: !tope,
    leidos: vistos.size,
  };
})();
