/*
 * Organic Story Engine runtime for HyperFrames episodes (vertical 1080x1920).
 *
 * One library for every episode: a camera that flies over the world map,
 * sprite actors driven by the paused GSAP timeline (seek-safe: every change is
 * a tween or a set at an absolute time), a 5x7 pixel font, fog and night.
 *
 * Usage inside an episode composition:
 *   const W = OSE.world({ tl, stage, map, manifest: window.OSE_MANIFEST,
 *                         base: "kit/", ink: "#fff4dc", accent: "#f3c75a" });
 *   W.cam.cut(0, [836, 470, 529]);  W.cam.move(2.6, 4, [835, 452, 230], "power2.inOut");
 *   const a = W.actor("habitante1", 812, 470);  a.loop(7, 13, ["chop_up","chop_down"], 5);
 *   W.label("LA GUERRA SE [ACERCA]", { at: 15.2, until: 20.3, y: 1260 });
 */
(function () {
  const OUT_W = 1080;
  const OUT_H = 1920;

  // ------------------------------------------------------------ pixel font
  // 5x7 house glyphs. Brackets in a label switch to the accent colour.
  const G = {
    A: [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    B: ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    C: [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    D: ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    E: ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    F: ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    G: [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."],
    H: ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    I: ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    J: ["..###", "...#.", "...#.", "...#.", "#..#.", "#..#.", ".##.."],
    K: ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    L: ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    M: ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    N: ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    O: [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    P: ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    Q: [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    R: ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    S: [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    T: ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    U: ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    V: ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    W: ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    X: ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    Y: ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    Z: ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": [".#.", "##.", ".#.", ".#.", ".#.", ".#.", "###"],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    "¿": ["..#..", ".....", "..#..", ".#...", "#....", "#...#", ".###."],
    "!": ["#", "#", "#", "#", "#", ".", "#"],
    "¡": ["#", ".", "#", "#", "#", "#", "#"],
    ":": [".", "#", ".", ".", ".", "#", "."],
    ".": [".", ".", ".", ".", ".", ".", "#"],
    ",": ["..", "..", "..", "..", "..", ".#", "#."],
    "-": ["...", "...", "...", "###", "...", "...", "..."],
    "_": ["....", "....", "....", "....", "....", "....", "####"],
    "+": [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    "=": [".....", ".....", "#####", ".....", "#####", ".....", "....."],
    "$": ["..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."],
    "←": [".......", "..#....", ".##....", "#######", ".##....", "..#....", "......."],
    "→": [".......", "....#..", "....##.", "#######", "....##.", "....#..", "......."],
    " ": ["...", "...", "...", "...", "...", "...", "..."],
    "Ñ": [".####", ".....", "#...#", "##..#", "#.#.#", "#..##", "#...#"],
    // Accented capitals: the full letter plus the accent two rows above it (rows 0-1 sit above the
    // line), so the outline can't swallow the accent into the top of the letter.
    "Á": ["...#.", ".....", ".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "É": ["...#.", ".....", "#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "Í": ["..#", "...", "###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    "Ó": ["...#.", ".....", ".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "Ú": ["...#.", ".....", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "%": ["##..#", "##..#", "...#.", "..#..", ".#...", "#..##", "#..##"],
    "#": [".....", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", "....."],
    "@": [".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."],
    "·": [".", ".", ".", "#", ".", ".", "."],
    "/": ["....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."],
  };

  // Lowercase for player nicknames (Minecraft-style tags). 9 rows: x-height
  // rows 2-6, ascenders from row 0, descenders on rows 7-8.
  const L = {
    a: [".....", ".....", ".###.", "....#", ".####", "#...#", ".####"],
    b: ["#....", "#....", "#.##.", "##..#", "#...#", "#...#", "####."],
    c: [".....", ".....", ".###.", "#....", "#....", "#....", ".###."],
    d: ["....#", "....#", ".##.#", "#..##", "#...#", "#...#", ".####"],
    e: [".....", ".....", ".###.", "#...#", "#####", "#....", ".###."],
    f: ["..##", ".#..", "####", ".#..", ".#..", ".#..", ".#.."],
    g: [".....", ".....", ".####", "#...#", "#...#", "#...#", ".####", "....#", "####."],
    h: ["#....", "#....", "#.##.", "##..#", "#...#", "#...#", "#...#"],
    i: ["#", ".", "#", "#", "#", "#", "#"],
    j: ["....#", ".....", "....#", "....#", "....#", "....#", "....#", "#...#", ".###."],
    k: ["#...", "#...", "#..#", "#.#.", "##..", "#.#.", "#..#"],
    l: ["#.", "#.", "#.", "#.", "#.", "#.", ".#"],
    m: [".....", ".....", "##.#.", "#.#.#", "#.#.#", "#...#", "#...#"],
    n: [".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"],
    o: [".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."],
    p: [".....", ".....", "####.", "#...#", "#...#", "#...#", "####.", "#....", "#...."],
    q: [".....", ".....", ".####", "#...#", "#...#", "#...#", ".####", "....#", "....#"],
    r: [".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."],
    s: [".....", ".....", ".####", "#....", ".###.", "....#", "####."],
    t: [".#..", ".#..", "####", ".#..", ".#..", ".#..", "..##"],
    u: [".....", ".....", "#...#", "#...#", "#...#", "#...#", ".####"],
    v: [".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    w: [".....", ".....", "#...#", "#...#", "#.#.#", "#.#.#", ".####"],
    x: [".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"],
    y: [".....", ".....", "#...#", "#...#", "#...#", "#...#", ".####", "....#", "####."],
    z: [".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"],
    _: [".....", ".....", ".....", ".....", ".....", ".....", ".....", ".....", "#####"],
  };

  /** Minecraft-style name tag: white glyphs on a translucent black plate. 1 canvas px = 1 font px. */
  function tagCanvas(text) {
    const glyph = (ch) => L[ch] || G[ch.toUpperCase()] || G[" "];
    const desc = [...text].some((ch) => (L[ch] || []).length > 7);
    const rows = desc ? 9 : 7;
    let w = 0;
    for (const ch of text) w += glyph(ch)[0].length + 1;
    w -= 1;
    const padX = 2;
    const padY = 1;
    const c = document.createElement("canvas");
    c.width = w + padX * 2;
    c.height = rows + padY * 2;
    const ctx = c.getContext("2d");
    ctx.fillStyle = "rgba(0, 0, 0, 0.42)";
    ctx.fillRect(0, 0, c.width, c.height);
    ctx.fillStyle = "#ffffff";
    let x = padX;
    for (const ch of text) {
      const g = glyph(ch);
      for (let gy = 0; gy < g.length; gy++) {
        for (let gx = 0; gx < g[gy].length; gx++) {
          if (g[gy][gx] === "#") ctx.fillRect(x + gx, padY + gy, 1, 1);
        }
      }
      x += g[0].length + 1;
    }
    return c;
  }

  const INK = "#fff4dc";
  const ACCENT = "#f3c75a";
  const EDGE = "#1d140e";

  function measure(text) {
    let w = 0;
    for (const ch of text) {
      if (ch === "[" || ch === "]") continue;
      const g = G[ch] || G[" "];
      w += g[0].length + 1;
    }
    return Math.max(0, w - 1);
  }

  /** Draws a label into a canvas. Units are font pixels × scale. */
  function pixelText(text, opt) {
    const s = opt.scale || 8;
    const ink = opt.ink || INK;
    const accent = opt.accent || ACCENT;
    const lines = text.split("\n");
    const widths = lines.map(measure);
    const maxW = Math.max(...widths);
    const lineH = 7 + (opt.leading == null ? 4 : opt.leading);
    const pad = 2; // outline + shadow room, in font pixels
    // room for accents above the first line (only when there are any, so other labels keep their size)
    const top = pad + (/[ÁÉÍÓÚ]/.test(lines[0]) ? 2 : 0);
    const cw = (maxW + pad * 2) * s;
    const ch = (lines.length * lineH - (lineH - 7) + pad + top + 1) * s;
    const c = document.createElement("canvas");
    c.width = cw;
    c.height = ch;
    const ctx = c.getContext("2d");
    // Paint pass: 0 = shadow, 1 = outline, 2 = fill
    for (let pass = 0; pass < 3; pass++) {
      lines.forEach((line, li) => {
        let x = pad + Math.round((maxW - widths[li]) / 2);
        const y = top + li * lineH;
        let hot = false;
        for (const chr of line) {
          if (chr === "[") { hot = true; continue; }
          if (chr === "]") { hot = false; continue; }
          const g = G[chr] || G[" "];
          const up = g.length - 7; // accent rows drawn above the line
          for (let gy = 0; gy < g.length; gy++) {
            for (let gx = 0; gx < g[gy].length; gx++) {
              if (g[gy][gx] !== "#") continue;
              const px = (x + gx) * s;
              const py = (y + gy - up) * s;
              // Outline and shadow keep a fixed weight so big numerals stay letters, not blocks.
              const o = Math.min(s, 7);
              const sh = Math.min(s, 9);
              if (pass === 0) {
                ctx.fillStyle = EDGE;
                ctx.fillRect(px - o, py + sh, s + o * 2, s + o); // drop shadow below
              } else if (pass === 1) {
                ctx.fillStyle = EDGE;
                ctx.fillRect(px - o, py - o, s + o * 2, s + o * 2);
              } else {
                ctx.fillStyle = hot ? accent : ink;
                ctx.fillRect(px, py, s, s);
              }
            }
          }
          x += g[0].length + 1;
        }
      });
    }
    return c;
  }

  // ------------------------------------------------------------ world
  function world(cfg) {
    const tl = cfg.tl;
    const stage = cfg.stage;
    const man = cfg.manifest;
    const base = cfg.base || "";

    const cam = document.createElement("div");
    cam.className = "ose-cam";
    const wld = document.createElement("div");
    wld.className = "ose-world";
    wld.style.width = cfg.map.w + "px";
    wld.style.height = cfg.map.h + "px";
    const img = document.createElement("img");
    img.src = base + cfg.map.src;
    img.className = "ose-map";
    img.width = cfg.map.w;
    img.height = cfg.map.h;
    wld.appendChild(img);
    cam.appendChild(wld);
    stage.appendChild(cam);

    const screen = document.createElement("div");
    screen.className = "ose-screen";
    stage.appendChild(screen);

    // Name tags keep a near-constant size on screen whatever the zoom:
    // every camera cut/move is logged and replayed onto each tag as an inverse scale.
    const camKeys = [];
    const plates = [];
    let camScaleNow = 1;
    const TAG_Q = 0.5; // world px per tag pixel at scale 1
    const tagScale = (s) => {
      const fpx = Math.max(2.2, Math.min(4, s * 0.75)); // output px per tag pixel
      return fpx / s / TAG_Q;
    };
    const TAG_MIN_SCALE = 2.6; // wider than this, tags would crowd each other: fade them out
    function applyCam(plate, k) {
      const sc = tagScale(k.s);
      const c = plate.firstChild;
      const on = k.s >= TAG_MIN_SCALE ? 1 : 0;
      if (k.dur) {
        tl.fromTo(plate, { scale: tagScale(k.s0) }, { scale: sc, duration: k.dur, ease: k.ease, immediateRender: false }, k.t);
        const was = k.s0 >= TAG_MIN_SCALE ? 1 : 0;
        if (was !== on) tl.to(c, { opacity: on, duration: k.dur * 0.3, ease: "none" }, on ? k.t + k.dur * 0.45 : k.t);
      } else {
        tl.set(plate, { scale: sc }, k.t);
        tl.set(c, { opacity: on }, k.t);
      }
    }

    function camVars(v) {
      return [{ x: OUT_W / 2, y: OUT_H / 2, scale: OUT_W / v[2] }, { x: -v[0], y: -v[1] }];
    }
    const camera = {
      cut(t, v) {
        const [o, i] = camVars(v);
        tl.set(cam, o, t);
        tl.set(wld, i, t);
        const k = { t, s: o.scale };
        camScaleNow = o.scale;
        camKeys.push(k);
        plates.forEach((p) => applyCam(p, k));
      },
      move(t, dur, v, ease) {
        const [o, i] = camVars(v);
        tl.to(cam, { ...o, duration: dur, ease: ease || "power2.inOut" }, t);
        tl.to(wld, { ...i, duration: dur, ease: ease || "power2.inOut" }, t);
        const k = { t, dur, ease: ease || "power2.inOut", s0: camScaleNow, s: o.scale };
        camScaleNow = o.scale;
        camKeys.push(k);
        plates.forEach((p) => applyCam(p, k));
      },
    };
    gsap.set(cam, { transformOrigin: "0 0" });

    // -------------------------------------------------- actors
    function actor(name, x, y, opt) {
      opt = opt || {};
      const m = man.sprites[name];
      if (!m) throw new Error("sprite missing: " + name);
      const S = opt.scale || cfg.spriteScale || 1.25;
      const el = document.createElement("div");
      el.className = "ose-sprite ose-" + name;
      el.style.width = m.w * S + "px";
      el.style.height = m.h * S + "px";
      el.style.backgroundImage = `url(${base}${m.file})`;
      el.style.backgroundSize = `${(m.frames.length * m.stride) * S}px ${m.h * S}px`;
      (opt.parent || wld).appendChild(el);
      const ax = m.anchor[0] * S;
      const ay = m.anchor[1] * S;
      const pos = (px, py) => ({ x: px - ax, y: py - ay, zIndex: Math.round(py * 10) });
      const bgp = (f) => {
        const i = m.frames.indexOf(f);
        if (i < 0) throw new Error(`${name}: no frame ${f}`);
        return `${-i * m.stride * S}px 0px`;
      };
      gsap.set(el, { ...pos(x, y), backgroundPosition: bgp(opt.frame || m.frames[0]), transformOrigin: `${ax}px ${ay}px` });
      if (opt.hidden) gsap.set(el, { autoAlpha: 0 });
      let tag = null;
      const tagPos = (px, py) => ({ x: px, y: py - m.h * S - 2 });
      const api = {
        el,
        frame(t, f) { tl.set(el, { backgroundPosition: bgp(f) }, t); return api; },
        loop(t0, t1, frames, fps) {
          const step = 1 / (fps || 6);
          let k = 0;
          for (let t = t0; t < t1 - 1e-6; t += step, k++) {
            tl.set(el, { backgroundPosition: bgp(frames[k % frames.length]) }, +t.toFixed(4));
          }
          return api;
        },
        seq(list) { list.forEach(([t, f]) => api.frame(t, f)); return api; },
        place(t, px, py) {
          tl.set(el, pos(px, py), t);
          if (tag) tl.set(tag, tagPos(px, py), t);
          return api;
        },
        move(t, dur, px, py, ease) {
          const p = pos(px, py);
          tl.to(el, { x: p.x, y: p.y, duration: dur, ease: ease || "none" }, t);
          tl.set(el, { zIndex: p.zIndex }, t + dur);
          if (tag) tl.to(tag, { ...tagPos(px, py), duration: dur, ease: ease || "none" }, t);
          return api;
        },
        /** Floating player name over the head. Call right after creating the actor. */
        nameplate(text) {
          const c = tagCanvas(text);
          tag = document.createElement("div");
          tag.className = "ose-tag";
          tag.style.width = c.width * TAG_Q + "px";
          tag.style.height = c.height * TAG_Q + "px";
          c.style.width = "100%";
          c.style.height = "100%";
          tag.appendChild(c);
          wld.appendChild(tag);
          gsap.set(tag, { ...tagPos(x, y), xPercent: -50, yPercent: -100, transformOrigin: "50% 100%", zIndex: 100000, scale: tagScale(camScaleNow) });
          if (opt.hidden) gsap.set(tag, { autoAlpha: 0 });
          plates.push(tag);
          camKeys.forEach((k) => applyCam(tag, k));
          return api;
        },
        flip(t, on) { tl.set(el, { scaleX: on ? -1 : 1 }, t); return api; },
        show(t) { tl.set(tag ? [el, tag] : el, { autoAlpha: 1 }, t); return api; },
        hide(t) { tl.set(tag ? [el, tag] : el, { autoAlpha: 0 }, t); return api; },
        hop(t, h) { // tiny vertical hop, for surprise or emphasis
          tl.to(tag ? [el, tag] : el, { y: `-=${h || 3}`, duration: 0.09, ease: "power1.out", yoyo: true, repeat: 1 }, t);
          return api;
        },
      };
      return api;
    }

    // -------------------------------------------------- campfire light
    function fireLight(x, y, t0, t1, rx, ry) {
      rx = rx || 30;
      ry = ry || 22;
      const el = document.createElement("div");
      el.className = "ose-firelight";
      el.style.width = rx * 2 + "px";
      el.style.height = ry * 2 + "px";
      wld.appendChild(el);
      gsap.set(el, { x: x - rx, y: y - ry, autoAlpha: 0, zIndex: 1 });
      tl.to(el, { autoAlpha: 1, duration: 0.5, ease: "power2.out" }, t0);
      // deterministic flicker
      let k = 0;
      for (let t = t0 + 0.5; t < t1; t += 0.125, k++) {
        const v = 0.82 + 0.18 * Math.sin(k * 2.3) * Math.cos(k * 0.7);
        tl.set(el, { scale: 0.96 + 0.06 * Math.sin(k * 1.7), opacity: v }, +t.toFixed(3));
      }
      return el;
    }

    // -------------------------------------------------- labels
    function label(text, opt) {
      const c = pixelText(text, Object.assign({ ink: cfg.ink, accent: cfg.accent }, opt));
      const el = document.createElement("div");
      el.className = "ose-label";
      el.appendChild(c);
      (opt.parent || screen).appendChild(el);
      const x = opt.x == null ? OUT_W / 2 : opt.x;
      gsap.set(el, { left: x, top: opt.y, xPercent: -50, yPercent: -50, autoAlpha: 0 });
      tl.set(el, { autoAlpha: 1 }, opt.at);
      if (opt.pop !== false) {
        tl.fromTo(el, { scale: 1.32 }, { scale: 1, duration: 0.24, ease: "back.out(3)" }, opt.at);
      }
      if (opt.until != null) tl.set(el, { autoAlpha: 0 }, opt.until);
      return el;
    }

    // -------------------------------------------------- icon (sprite in screen space)
    function icon(name, x, y, scale, at, until) {
      const m = man.sprites[name];
      const a = actor(name, x + m.anchor[0] * scale, y + m.anchor[1] * scale, { scale, parent: screen, hidden: true });
      a.el.classList.add("ose-icon");
      a.show(at);
      tl.fromTo(a.el, { y: `-=${scale * 2}` }, { y: `+=${scale * 2}`, duration: 0.25, ease: "back.out(3)" }, at);
      if (until != null) a.hide(until);
      return a;
    }

    // -------------------------------------------------- fog + night
    function fogLayer(file, opt) {
      const el = document.createElement("div");
      el.className = "ose-fog";
      el.setAttribute("data-layout-allow-overflow", "");
      el.style.backgroundImage = `url(${base}${file})`;
      el.style.backgroundSize = `${opt.tile}px ${opt.tile}px`;
      if (opt.mask) {
        el.style.webkitMaskImage = opt.mask;
        el.style.maskImage = opt.mask;
      }
      screen.appendChild(el);
      gsap.set(el, { opacity: opt.opacity == null ? 0.8 : opt.opacity, backgroundPosition: "0px 0px" });
      tl.to(el, { backgroundPosition: `${opt.dx}px ${opt.dy}px`, duration: opt.duration, ease: "none" }, 0);
      return el;
    }

    function night() {
      const el = document.createElement("div");
      el.className = "ose-night";
      el.setAttribute("data-layout-allow-overflow", "");
      screen.appendChild(el);
      gsap.set(el, { autoAlpha: 0, scale: 1.4 });
      return el;
    }

    return { cam: camera, actor, label, icon, fireLight, fogLayer, night, screen, world: wld, pixelText };
  }

  window.OSE = { world, pixelText, tagCanvas, OUT_W, OUT_H };
})();
