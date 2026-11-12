// Runs in the page world (MAIN) before TikTok. It only READS the notification responses the page
// itself requests and hands them to the extension script. It never changes requests or responses.
(() => {
  if (window.__hsCensoEscucha) return;
  window.__hsCensoEscucha = true;
  const RUTA = /\/api\/notice\/multi\//;
  const pasar = (url, texto) => {
    if (texto && texto.length < 5e6) window.postMessage({ __hsCenso: 1, url: String(url), texto }, location.origin);
  };

  const fetchOriginal = window.fetch;
  window.fetch = function (...args) {
    const p = fetchOriginal.apply(this, args);
    try {
      const url = typeof args[0] === "string" ? args[0] : args[0] && args[0].url;
      if (url && RUTA.test(url)) p.then((r) => r.clone().text().then((t) => pasar(url, t))).catch(() => {});
    } catch {}
    return p;
  };

  const abrir = XMLHttpRequest.prototype.open;
  const enviar = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (metodo, url, ...resto) {
    this.__hsUrl = url;
    return abrir.call(this, metodo, url, ...resto);
  };
  XMLHttpRequest.prototype.send = function (...args) {
    if (this.__hsUrl && RUTA.test(String(this.__hsUrl))) {
      this.addEventListener("load", () => {
        try {
          if (this.responseType === "" || this.responseType === "text") pasar(this.__hsUrl, this.responseText);
        } catch {}
      });
    }
    return enviar.apply(this, args);
  };
})();
