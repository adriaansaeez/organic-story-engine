-- Organic Story Engine: the audience database (SQLite, one local file).
-- The ideas behind each table are explained in docs/audience-db.md.

-- Every follower is a citizen of the world. The id IS the arrival order:
-- citizen #1 followed first, and that number never changes once published.
CREATE TABLE IF NOT EXISTS citizens (
  id         INTEGER PRIMARY KEY,
  handle     TEXT NOT NULL UNIQUE,        -- lowercase platform handle, no @
  name       TEXT,                        -- display name, if known
  role       TEXT NOT NULL,               -- job in the world, assigned by quota (world.json "roles")
  look_seed  INTEGER NOT NULL,            -- FNV-1a hash of the handle: same handle, same look, forever
  joined     TEXT NOT NULL DEFAULT (date('now')),
  batch      TEXT,                        -- which import brought them in
  hidden     INTEGER NOT NULL DEFAULT 0,  -- opted out / blocked: never drawn
  notes      TEXT
);
CREATE INDEX IF NOT EXISTS citizens_role ON citizens(role);

-- Published videos (episodes and short stories).
CREATE TABLE IF NOT EXISTS videos (
  id         TEXT PRIMARY KEY,            -- ep01, short01...
  title      TEXT,
  published  TEXT,
  url        TEXT
);

-- Who appears in which video, and how. Protagonists are the people the story is about.
CREATE TABLE IF NOT EXISTS appearances (
  citizen_id INTEGER NOT NULL REFERENCES citizens(id) ON DELETE CASCADE,
  video_id   TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  part       TEXT NOT NULL DEFAULT 'background',   -- protagonist | background | nameplate
  PRIMARY KEY (citizen_id, video_id)
);
CREATE INDEX IF NOT EXISTS appearances_video ON appearances(video_id);

-- What the community asked for in the comments. One per person per video: their FIRST comment, verbatim.
CREATE TABLE IF NOT EXISTS requests (
  id           INTEGER PRIMARY KEY,
  handle       TEXT NOT NULL,
  citizen_id   INTEGER REFERENCES citizens(id) ON DELETE SET NULL,
  video_id     TEXT REFERENCES videos(id) ON DELETE SET NULL,   -- where it was asked
  source       TEXT NOT NULL DEFAULT 'comment',                 -- comment | live | dm | other
  url          TEXT,
  kind         TEXT NOT NULL DEFAULT 'other',                   -- role | action | build | event | other
  text         TEXT NOT NULL,
  target       TEXT,                                            -- handle it affects, if any
  likes        INTEGER NOT NULL DEFAULT 0,                      -- community priority
  route        TEXT,                                            -- which canon route it pushes, if any
  status       TEXT NOT NULL DEFAULT 'pending',                 -- pending | accepted | fulfilled | rejected | duplicate
  fulfilled_in TEXT REFERENCES videos(id) ON DELETE SET NULL,
  reply        TEXT,
  created      TEXT NOT NULL DEFAULT (datetime('now')),
  updated      TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (video_id, handle)
);
CREATE INDEX IF NOT EXISTS requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS requests_handle ON requests(handle);
