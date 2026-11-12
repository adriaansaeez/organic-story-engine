// Pure logic of the extension (no Chrome APIs, so node can test it).
// Pulls follows out of a TikTok /api/notice/multi/ response (group 7 = followers) and builds the export
// file that `engine/audience/audience.py import` reads.
(function (raiz) {
  const GRUPO_SEGUIDORES = 7;

  /** -> { seguidores: [{usuario, nombre, ts}], meta: {total, hayMas} | null } */
  function extraerNotificaciones(json) {
    const seguidores = [];
    let meta = null;
    for (const g of (json && json.notice_lists) || []) {
      if (g.group !== GRUPO_SEGUIDORES) continue;
      meta = { total: Number(g.total) || 0, hayMas: !!g.has_more };
      for (const n of g.notice_list || []) {
        const u = n && n.follow && n.follow.from_user;
        if (!u || !u.unique_id || !n.create_time) continue;
        seguidores.push({ usuario: String(u.unique_id).toLowerCase(), nombre: u.nickname || null, ts: Number(n.create_time) });
      }
    }
    return { seguidores, meta };
  }

  /** Merge without duplicates. Someone who appears twice (re-follow) keeps their OLDEST follow. */
  function mezclar(guardados, nuevos) {
    const out = { ...guardados };
    let añadidos = 0;
    for (const s of nuevos) {
      const prev = out[s.usuario];
      if (!prev) { out[s.usuario] = { nombre: s.nombre, ts: s.ts }; añadidos++; }
      else if (s.ts < prev.ts) out[s.usuario] = { nombre: s.nombre || prev.nombre, ts: s.ts };
    }
    return { seguidores: out, añadidos };
  }

  const TZ = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const fechaLocal = (ts) => new Date(ts * 1000).toLocaleDateString("sv-SE", { timeZone: TZ });

  /** Sorted list (oldest -> newest). With `despuesDe` (a handle already in the census) only later follows. */
  function exportar(seguidores, { despuesDe, total, ahora = new Date() } = {}) {
    let filas = Object.entries(seguidores)
      .map(([usuario, s]) => ({ usuario, nombre: s.nombre, ts: s.ts }))
      .sort((a, b) => a.ts - b.ts || (a.usuario < b.usuario ? -1 : 1));
    let corte = null;
    if (despuesDe) {
      const u = String(despuesDe).trim().replace(/^@/, "").toLowerCase();
      const ref = seguidores[u];
      if (!ref) return { error: `@${u} is not among the captured followers` };
      corte = u;
      filas = filas.filter((f) => f.ts > ref.ts);
    }
    const hoy = ahora.toLocaleDateString("sv-SE", { timeZone: TZ });
    return {
      batch: `${hoy} extension`,
      source: "Organic Story Engine capture extension (TikTok notifications)" + (corte ? `, after @${corte}` : ""),
      captured: ahora.toISOString(),
      platform_total: total || null,
      followers: filas.map((f) => ({ handle: f.usuario, name: f.nombre, joined: fechaLocal(f.ts), ts: f.ts })),
    };
  }

  const api = { extraerNotificaciones, mezclar, exportar, fechaLocal };
  if (typeof module === "object" && module.exports) module.exports = api;
  else raiz.HSCenso = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
