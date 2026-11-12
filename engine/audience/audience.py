#!/usr/bin/env python3
"""The audience database: followers -> citizens, comments -> requests, videos -> appearances.

One local SQLite file (default ./audience.db, or $OSE_DB, or --db). Every write
previews first and only touches the database with --confirm.

  audience.py init
  audience.py import FOLLOWERS.json --world W [--confirm]       followers -> citizens, in arrival order
  audience.py from-export TIKTOK_EXPORT(.zip|.json|.txt) [--since YYYY-MM-DD]
  audience.py requests COMMENTS.json --world W [--census] [--confirm]
  audience.py comments [VIDEO] [--all] [--sort likes|time] [--user H] [--search T] [--status S] [--json]
  audience.py fulfil REQUEST_ID --in VIDEO [--target H] [--route R] [--reply TEXT] [--confirm]
  audience.py appear HANDLE VIDEO [--part protagonist|background|nameplate] [--confirm]
  audience.py roster [--video V] [--json]                        citizens for the crowd layer

Files are the ones the capture tools write (engine/capture/): a followers file
is {"batch": "...", "followers": ["a", {"handle": "b", "name": "B", "ts": 1731000000}]}
and a comments file is {"video": "<platform id>", "url": "...", "title": "...",
"comments": [{"handle", "text", "likes", "ts"}]}. Older Spanish keys from the
original project (usuarios/usuario/nombre/lote, comentarios/usuario/texto) are
accepted too.
"""
import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import date, datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from roles import assign_role, load_world, look_seed, normalize_handle  # noqa: E402


# ------------------------------------------------------------------ db
def connect(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    with open(os.path.join(HERE, "schema.sql"), encoding="utf-8") as f:
        db.executescript(f.read())
    return db


def one(db, sql, *args):
    r = db.execute(sql, args).fetchone()
    return r[0] if r else None


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def field(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, ""):
            return d[k]
    return default


# ------------------------------------------------------------------ followers -> citizens
def plan_citizens(db, roles, entries, batch):
    """Return (new_rows, already, invalid). Rows carry their final id, role and look seed."""
    # entries with a follow timestamp are sorted by it (the capture extension records it)
    if any(isinstance(e, dict) and isinstance(e.get("ts"), (int, float)) for e in entries):
        entries = [e for _, e in sorted(enumerate(entries), key=lambda p: (
            p[1]["ts"] if isinstance(p[1], dict) and isinstance(p[1].get("ts"), (int, float)) else float("inf"), p[0]))]
    existing = {r[0] for r in db.execute("SELECT handle FROM citizens")}
    counts = {r[0]: r[1] for r in db.execute("SELECT role, count(*) FROM citizens GROUP BY role")}
    next_id = one(db, "SELECT coalesce(max(id), 0) FROM citizens")
    seen, new, already, invalid = set(), [], [], []
    for e in entries:
        raw = e if isinstance(e, str) else field(e, "handle", "usuario")
        h = normalize_handle(raw)
        if not h:
            invalid.append(raw)
            continue
        if h in seen:
            continue
        seen.add(h)
        if h in existing:
            already.append(h)
            continue
        next_id += 1
        name = field(e, "name", "nombre") if isinstance(e, dict) else None
        new.append({"id": next_id, "handle": h, "name": str(name)[:60] if name else None,
                    "role": assign_role(roles, counts), "look_seed": look_seed(h), "batch": batch})
    return new, already, invalid


def cmd_import(a, db):
    world = load_world(a.world)
    data = load(a.file)
    entries = field(data, "followers", "usuarios", default=[])
    batch = str(field(data, "batch", "lote", default=None) or (re.search(r"\d{4}-\d{2}-\d{2}", a.file) or [date.today().isoformat()])[0])
    new, already, invalid = plan_citizens(db, world["roles"], entries, batch)
    print(f"batch {batch}: {len(new)} new, {len(already)} already in, {len(invalid)} invalid")
    if invalid:
        print("  invalid:", ", ".join(map(str, invalid)))
    if new:
        print(f"  from #{new[0]['id']} (@{new[0]['handle']}) to #{new[-1]['id']} (@{new[-1]['handle']})")
    if not a.confirm or not new:
        if new:
            print("Preview only. Add --confirm to write them.")
        return
    with db:
        db.executemany("INSERT INTO citizens (id, handle, name, role, look_seed, batch) VALUES "
                       "(:id, :handle, :name, :role, :look_seed, :batch)", new)
        db.execute("UPDATE requests SET citizen_id = (SELECT id FROM citizens c WHERE c.handle = requests.handle) "
                   "WHERE citizen_id IS NULL")
    print(f"Done: {len(new)} new citizens.")


# ------------------------------------------------------------------ official data export -> followers file
def cmd_from_export(a, _db):
    texts = []
    if a.file.lower().endswith(".zip"):
        names = subprocess.run(["unzip", "-Z1", a.file], capture_output=True, text=True, check=True).stdout.split()
        picked = [n for n in names if n.lower().endswith(".json") or "follower" in n.lower()]
        texts = [subprocess.run(["unzip", "-p", a.file, n], capture_output=True, text=True, check=True).stdout for n in picked]
    else:
        with open(a.file, encoding="utf-8") as f:
            texts = [f.read()]
    found = []

    def walk(node, path):
        if isinstance(node, list):
            for x in node:
                if isinstance(x, dict):
                    low = {k.lower(): v for k, v in x.items()}
                    u = low.get("username") or low.get("user_name") or low.get("uniqueid")
                    d = low.get("date") or low.get("time")
                    if u and d and "follower" in path.lower():
                        found.append((str(d), u))
                walk(x, path)
        elif isinstance(node, dict):
            for k, v in node.items():
                walk(v, path + "/" + k)

    for t in texts:
        try:
            walk(json.loads(t), "")
        except json.JSONDecodeError:  # .txt export: "Date: ...\nUsername: ..." blocks
            for d, u in re.findall(r"Date:\s*(.+?)\s*\n\s*Username:\s*(\S+)", t):
                found.append((d, u))
    found.sort()
    if a.since:
        found = [f for f in found if f[0][:10] >= a.since]
    out = {"batch": f"{date.today().isoformat()} export", "source": "official data export (oldest first)",
           "followers": [{"handle": u, "joined": d[:10]} for d, u in found]}
    os.makedirs("data/imports", exist_ok=True)
    path = f"data/imports/{date.today().isoformat()}-export.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(f"{len(found)} followers -> {path}")


# ------------------------------------------------------------------ comments -> requests
def cmd_requests(a, db):
    world = load_world(a.world)
    account = world.get("account", "").lower()
    data = load(a.file)
    vid_ext = str(field(data, "video", default="") or (re.search(r"/video/(\d+)", str(data.get("url", ""))) or ["", ""])[1])
    if not re.match(r"^\d{8,}$", vid_ext):
        sys.exit("The file has no platform video id (field 'video' or 'url').")
    url = f"https://www.tiktok.com/@{account}/video/{vid_ext}" if account else data.get("url")
    video = one(db, "SELECT id FROM videos WHERE url LIKE ?", f"%/video/{vid_ext}%")
    new_video = None
    if not video:
        prefix = world.get("episode_prefix", "ep")
        nums = [int(m.group(1)) for (i,) in db.execute("SELECT id FROM videos") if (m := re.match(rf"^{prefix}(\d+)$", i))]
        video = f"{prefix}{max(nums, default=0) + 1:02d}"
        published = datetime.fromtimestamp(int(vid_ext) >> 32, tz=timezone.utc).date().isoformat()  # ids embed the post time
        new_video = (video, str(field(data, "title", "titulo", default=video))[:120], published, url)

    comments = sorted(field(data, "comments", "comentarios", default=[]),
                      key=lambda c: c.get("ts") if isinstance(c.get("ts"), (int, float)) else float("inf"))
    first = {}
    for c in comments:
        h = str(field(c, "handle", "usuario", default="")).strip().lstrip("@").lower()
        text = str(field(c, "text", "texto", default="")).strip()
        if not h or h == account or not text or h in first:
            continue
        first[h] = {"text": text, "likes": int(c.get("likes") or 0), "ts": c.get("ts")}

    have = {} if new_video else {r["handle"]: r["likes"] for r in db.execute("SELECT handle, likes FROM requests WHERE video_id = ?", (video,))}
    new = [(h, c) for h, c in first.items() if h not in have]
    liked = [(h, c) for h, c in first.items() if h in have and have[h] != c["likes"]]
    census = {r[0] for r in db.execute("SELECT handle FROM citizens")}
    outside = [h for h in first if h not in census]

    print(f"video {video}{' (NEW)' if new_video else ''} - {len(comments)} comments from {len(first)} people")
    print(f"  {len(new)} new requests, {len(have)} already had theirs, {len(liked)} like counts refreshed")
    if outside:
        print(f"  {len(outside)} authors are not citizens{' and will be added' if a.census else ' (add --census to add them)'}")
    for h, c in new[:15]:
        print(f"  + @{h}: {' '.join(c['text'].split())[:70]}")
    if not a.confirm:
        print("Preview only. Add --confirm to write.")
        return
    with db:
        if new_video:
            db.execute("INSERT INTO videos (id, title, published, url) VALUES (?, ?, ?, ?)", new_video)
        for h, c in new:
            db.execute("INSERT INTO requests (handle, citizen_id, video_id, source, url, kind, text, likes) VALUES "
                       "(?, (SELECT id FROM citizens WHERE handle = ?), ?, 'comment', ?, 'other', ?, ?)",
                       (h, h, video, url, c["text"], c["likes"]))
        for h, c in liked:  # never overwrite a request: only its likes move
            db.execute("UPDATE requests SET likes = ?, updated = datetime('now') WHERE video_id = ? AND handle = ?",
                       (c["likes"], video, h))
        if a.census and outside:  # unknown authors join the census in the order of their first comment
            rows, _, _ = plan_citizens(db, world["roles"], [{"handle": h} for h in outside], f"comments {video}")
            db.executemany("INSERT INTO citizens (id, handle, name, role, look_seed, batch) VALUES "
                           "(:id, :handle, :name, :role, :look_seed, :batch)", rows)
        db.execute("UPDATE requests SET citizen_id = (SELECT id FROM citizens c WHERE c.handle = requests.handle) "
                   "WHERE citizen_id IS NULL")
    print(f"Done: {len(new)} new requests in {video}.")


# ------------------------------------------------------------------ reading
def resolve_video(db, target):
    ext = re.search(r"(\d{15,})", target)
    row = db.execute("SELECT * FROM videos WHERE url LIKE ?", (f"%/video/{ext.group(1)}%",)).fetchone() if ext \
        else db.execute("SELECT * FROM videos WHERE id = ?", (target.lower(),)).fetchone()
    if not row:
        sys.exit(f'Unknown video "{target}". Run without arguments to list them.')
    return row


def cmd_comments(a, db):
    if not a.video:
        rows = db.execute("SELECT v.id, v.title, v.published, v.url, count(r.id) AS n, "
                          "sum(r.status = 'pending') AS pending FROM videos v LEFT JOIN requests r ON r.video_id = v.id "
                          "GROUP BY v.id ORDER BY v.published DESC, v.id DESC").fetchall()
        if a.json:
            print(json.dumps([dict(r) for r in rows], indent=1, ensure_ascii=False))
            return
        for r in rows:
            print(f"{r['id']}  {r['published'] or '?'}  {r['n']} requests ({r['pending'] or 0} pending)  {r['title'] or ''}\n      {r['url'] or 'no url'}")
        return
    v = resolve_video(db, a.video)
    if a.all:  # raw capture: every comment, not just the first per person
        ext = (re.search(r"/video/(\d+)", v["url"] or "") or [None, None])[1]
        caps = sorted(f for f in os.listdir(a.captures) if ext and f.endswith(f"-{ext}.json")) if os.path.isdir(a.captures) else []
        if not caps:
            sys.exit(f"No captures of {v['id']} in {a.captures}/ (*-{ext}.json). Capture them first (skill ose-comments).")
        data = load(os.path.join(a.captures, caps[-1]))
        rows = [{"handle": field(c, "handle", "usuario"), "text": field(c, "text", "texto"), "likes": c.get("likes", 0),
                 "ts": c.get("ts")} for c in field(data, "comments", "comentarios", default=[])]
    else:
        sql = ("SELECT r.id, r.handle, c.id AS num, c.role, r.text, r.likes, r.status, r.route, r.reply, r.created "
               "FROM requests r LEFT JOIN citizens c ON c.id = r.citizen_id WHERE r.video_id = ?")
        args = [v["id"]]
        if a.status:
            sql += " AND r.status = ?"
            args.append(a.status)
        rows = [dict(r) for r in db.execute(sql, args)]
    if a.user:
        rows = [r for r in rows if r["handle"] == a.user.lstrip("@").lower()]
    if a.search:
        rows = [r for r in rows if a.search.lower() in str(r["text"]).lower()]
    key = (lambda r: (r.get("ts") or r.get("id") or 0)) if a.sort == "time" else (lambda r: (-int(r["likes"] or 0), r.get("ts") or r.get("id") or 0))
    rows.sort(key=key)
    if a.json:
        print(json.dumps(rows, indent=1, ensure_ascii=False))
        return
    print(f"{v['id']} - {v['title'] or ''} - {len(rows)} rows", file=sys.stderr)
    for r in rows:
        who = f"@{r['handle']}" + (f" #{r['num']}" if r.get("num") else "")
        extra = f" [{r['status']}{', ' + r['route'] if r.get('route') else ''}]" if r.get("status") else ""
        print(f"{int(r['likes'] or 0):>4} likes  {who}{extra}: {' '.join(str(r['text']).split())}")


def cmd_roster(a, db):
    if a.video:
        rows = db.execute("SELECT c.id, c.handle, c.role, c.look_seed, a.part FROM citizens c JOIN appearances a "
                          "ON a.citizen_id = c.id WHERE a.video_id = ? AND c.hidden = 0 ORDER BY c.id", (a.video,)).fetchall()
    else:
        rows = db.execute("SELECT id, handle, role, look_seed FROM citizens WHERE hidden = 0 ORDER BY id").fetchall()
    rows = [dict(r) for r in rows]
    if a.json:
        print(json.dumps(rows, ensure_ascii=False))
        return
    counts = {}
    for r in rows:
        counts[r["role"]] = counts.get(r["role"], 0) + 1
    print(f"{len(rows)} citizens: " + ", ".join(f"{k} {n}" for k, n in sorted(counts.items(), key=lambda p: -p[1])))


# ------------------------------------------------------------------ writing story outcomes
def cmd_fulfil(a, db):
    r = db.execute("SELECT * FROM requests WHERE id = ?", (a.request,)).fetchone()
    if not r:
        sys.exit(f"No request #{a.request}.")
    if not one(db, "SELECT 1 FROM videos WHERE id = ?", a.into):
        sys.exit(f"Video {a.into} is not registered yet (it appears after its first comment capture, or add it with `appear`).")
    target = normalize_handle(a.target) if a.target else r["target"]
    who = [h for h in (r["handle"], target) if h]
    print(f"#{r['id']} @{r['handle']}: {r['text']}\n  -> fulfilled in {a.into}; protagonists: {', '.join('@' + h for h in who)}")
    if not a.confirm:
        print("Preview only. Add --confirm to write.")
        return
    with db:
        db.execute("UPDATE requests SET status = 'fulfilled', fulfilled_in = ?, route = coalesce(?, route), "
                   "reply = coalesce(?, reply), target = coalesce(?, target), updated = datetime('now') WHERE id = ?",
                   (a.into, a.route, a.reply, target, r["id"]))
        for h in who:  # the requester and the target become protagonists of that video
            db.execute("INSERT INTO appearances (citizen_id, video_id, part) SELECT id, ?, 'protagonist' FROM citizens "
                       "WHERE handle = ? ON CONFLICT (citizen_id, video_id) DO UPDATE SET part = 'protagonist'", (a.into, h))
    print("Done.")


def cmd_appear(a, db):
    h = normalize_handle(a.handle)
    cid = one(db, "SELECT id FROM citizens WHERE handle = ?", h)
    if not cid:
        sys.exit(f"@{h} is not a citizen.")
    print(f"@{h} (#{cid}) -> {a.video} as {a.part}")
    if not a.confirm:
        print("Preview only. Add --confirm to write.")
        return
    with db:
        db.execute("INSERT OR IGNORE INTO videos (id) VALUES (?)", (a.video,))
        db.execute("INSERT INTO appearances (citizen_id, video_id, part) VALUES (?, ?, ?) "
                   "ON CONFLICT (citizen_id, video_id) DO UPDATE SET part = excluded.part", (cid, a.video, a.part))
    print("Done.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=os.environ.get("OSE_DB", "audience.db"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    p = sub.add_parser("import"); p.add_argument("file"); p.add_argument("--world", required=True); p.add_argument("--confirm", action="store_true")
    p = sub.add_parser("from-export"); p.add_argument("file"); p.add_argument("--since")
    p = sub.add_parser("requests"); p.add_argument("file"); p.add_argument("--world", required=True)
    p.add_argument("--census", action="store_true"); p.add_argument("--confirm", action="store_true")
    p = sub.add_parser("comments"); p.add_argument("video", nargs="?"); p.add_argument("--all", action="store_true")
    p.add_argument("--sort", choices=("likes", "time"), default="likes"); p.add_argument("--user"); p.add_argument("--search")
    p.add_argument("--status"); p.add_argument("--json", action="store_true"); p.add_argument("--captures", default="data/comments")
    p = sub.add_parser("fulfil"); p.add_argument("request", type=int); p.add_argument("--in", dest="into", required=True)
    p.add_argument("--route"); p.add_argument("--reply"); p.add_argument("--target", help="handle the request is about")
    p.add_argument("--confirm", action="store_true")
    p = sub.add_parser("appear"); p.add_argument("handle"); p.add_argument("video")
    p.add_argument("--part", choices=("protagonist", "background", "nameplate"), default="background"); p.add_argument("--confirm", action="store_true")
    p = sub.add_parser("roster"); p.add_argument("--video"); p.add_argument("--json", action="store_true")
    a = ap.parse_args()

    db = connect(a.db)
    {"init": lambda a, db: print("audience db ready:", os.path.abspath(a.db)), "import": cmd_import,
     "from-export": cmd_from_export, "requests": cmd_requests, "comments": cmd_comments, "fulfil": cmd_fulfil,
     "appear": cmd_appear, "roster": cmd_roster}[a.cmd](a, db)


if __name__ == "__main__":
    main()
