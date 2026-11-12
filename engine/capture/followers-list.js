// Safety net for the census: the profile's "Followers" list (the ~30 most recent). Grouped
// notifications ("X and 2 others followed you") can skip people; this list does not.
// Evaluate INSIDE https://www.tiktok.com/@<account> prefixed with `await `, with
// window.__censo = [handles already registered]. Read-only: opens the modal, reads it, closes it.
//
// Returns { faltan: [handles missing, oldest first], leidos, total }, ready to import.
(async () => {
  const conocidos = new Set((window.__censo || []).map((u) => String(u).toLowerCase()));
  const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
  const visible = (e) => e && e.getBoundingClientRect().height > 0;
  const modal = () => [...document.querySelectorAll('[role="dialog"]')].find((d) => visible(d) && d.querySelector("li a[href^='/@']"));

  if (!modal()) {
    const abrir = document.querySelector('[data-e2e="followers-count"]')
      || [...document.querySelectorAll("span, strong, div, p")].find((e) => e.childElementCount === 0 && visible(e) && /^(Seguidores|Followers)$/.test(e.textContent.trim()));
    if (!abrir) return { error: "No encuentro el contador de Seguidores en el perfil." };
    abrir.click();
    for (let i = 0; i < 20 && !modal(); i++) await dormir(400);
  }
  const m = modal();
  if (!m) return { error: "No se abre la lista de Seguidores." };
  await dormir(1500);

  const lista = [];
  for (const li of m.querySelectorAll("li")) {
    const a = li.querySelector('a[href^="/@"]');
    const u = a && a.getAttribute("href").slice(2).split(/[/?]/)[0].toLowerCase();
    if (u && !lista.includes(u)) lista.push(u);
  }
  const total = Number((m.innerText.match(/Seguidores\s*([\d.]+)/) || [])[1]?.replace(/\./g, "")) || null;

  // cerrar sin tocar nada más
  const cerrar = [...m.querySelectorAll("button, [role='button']")].find((b) => /cerrar|close/i.test(b.getAttribute("aria-label") || ""));
  if (cerrar) cerrar.click(); else document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));

  return { faltan: lista.filter((u) => !conocidos.has(u)).reverse(), leidos: lista.length, total };
})();
