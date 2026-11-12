// node engine/capture/extension/prueba/probar.mjs : tests extraer.js on a trimmed, anonymised real response
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
const require = createRequire(import.meta.url);
const { extraerNotificaciones, mezclar, exportar } = require("../extraer.js");
const r = JSON.parse(readFileSync(new URL("./notice.json", import.meta.url)));

const { seguidores, meta } = extraerNotificaciones(r);
assert.deepEqual(meta, { total: 453, hayMas: true });
assert.equal(seguidores.length, 4, "ignores group 2 and the entry without a user");
assert.ok(seguidores.every((s) => s.usuario === s.usuario.toLowerCase()));

let { seguidores: todos, añadidos } = mezclar({}, seguidores);
assert.equal(añadidos, 3, "herrero.koldo appears twice");
assert.equal(todos["herrero.koldo"].ts, 1794150000, "keeps the oldest follow");
({ añadidos } = mezclar(todos, seguidores));
assert.equal(añadidos, 0, "receiving the same again adds nothing");

const ex = exportar(todos, { total: 453, ahora: new Date("2026-11-08T21:00:00Z") });
assert.deepEqual(ex.followers.map((u) => u.handle), ["herrero.koldo", "luna.del.norte", "molinera_ana"], "oldest -> newest");
assert.equal(ex.followers[0].joined, "2026-11-08");
assert.equal(ex.batch, "2026-11-08 extension");
const corte = exportar(todos, { despuesDe: "@Luna.Del.Norte" });
assert.deepEqual(corte.followers.map((u) => u.handle), ["molinera_ana"], "only after the last registered");
assert.ok(exportar(todos, { despuesDe: "nadie" }).error);
console.log("extraer.js: all good");
