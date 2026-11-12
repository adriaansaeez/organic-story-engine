/* global HSCenso */
const $ = (id) => document.getElementById(id);
// Your series account. Change this one line for your own channel.
const PERFIL = "https://www.tiktok.com/@your_account";
let pestana = null;

const hora = (ts) =>
  new Date(ts * 1000).toLocaleString(undefined, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

async function pintar() {
  const { seguidores = {}, meta = {}, recogiendo } = await chrome.storage.local.get(["seguidores", "meta", "recogiendo"]);
  const ts = Object.values(seguidores).map((s) => s.ts).sort((a, b) => a - b);
  $("n").textContent = ts.length;
  $("n-texto").textContent = ts.length === 1 ? "follower captured" : "followers captured";
  $("rango").textContent = ts.length ? `from ${hora(ts[0])} to ${hora(ts.at(-1))}` : "Press Collect with TikTok open.";
  $("aviso").textContent =
    meta.total && meta.total > ts.length
      ? `TikTok counts ${meta.total} followers. If collecting brings no more, older ones only come with the official data export.`
      : "";
  $("descargar").disabled = !ts.length;
  $("recoger").disabled = !!recogiendo;
  $("recoger").textContent = recogiendo ? "Collecting…" : "Collect followers";
}

async function init() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const enTikTok = tab && /^https:\/\/www\.tiktok\.com\//.test(tab.url || "");
  pestana = enTikTok ? tab : null;
  $("dentro").hidden = !enTikTok;
  $("fuera").hidden = enTikTok;
  await pintar();
}

$("abrir").addEventListener("click", () => chrome.tabs.create({ url: PERFIL }));

$("recoger").addEventListener("click", async () => {
  if (!pestana) return;
  $("estado").textContent = "Opening notifications and scrolling the list. You can close this: it keeps going.";
  try {
    const r = await chrome.tabs.sendMessage(pestana.id, { tipo: "recoger" });
    $("estado").textContent = r && r.ok
      ? (r.nuevos ? `Done: ${r.nuevos} new.` : "Done: nothing new.")
      : (r && r.error) || "Could not collect.";
  } catch {
    $("estado").textContent = "Reload the TikTok tab (the extension was installed after it opened) and try again.";
  }
  pintar();
});

$("descargar").addEventListener("click", async () => {
  $("error").textContent = "";
  const { seguidores = {}, meta = {} } = await chrome.storage.local.get(["seguidores", "meta"]);
  const datos = HSCenso.exportar(seguidores, { despuesDe: $("despues").value, total: meta.total });
  if (datos.error) { $("error").textContent = datos.error; return; }
  if (!datos.followers.length) { $("error").textContent = "Nobody after that handle."; return; }
  const url = URL.createObjectURL(new Blob([JSON.stringify(datos, null, 1) + "\n"], { type: "application/json" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = `followers-${datos.batch.slice(0, 10)}.json`;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
});

let confirmando = null;
$("vaciar").addEventListener("click", async () => {
  const b = $("vaciar");
  if (!confirmando) {
    b.textContent = "Press again to clear";
    b.classList.add("confirmar");
    confirmando = setTimeout(() => { b.textContent = "Clear captured"; b.classList.remove("confirmar"); confirmando = null; }, 3000);
    return;
  }
  clearTimeout(confirmando);
  confirmando = null;
  b.textContent = "Clear captured";
  b.classList.remove("confirmar");
  await chrome.storage.local.remove(["seguidores", "meta"]);
  pintar();
});

chrome.storage.onChanged.addListener(pintar);
init();
