"""Roles, looks and handles: the rules that turn a follower into a citizen.

Roles come from <world>/world.json:

  "roles": [{"id": "woodcutter", "quota": 0.22}, {"id": "gatherer", "quota": 0.22}, ...]

A new citizen gets the role that is furthest below its quota, so the village
keeps the proportions the story needs no matter how fast it grows.
"""
import json
import os
import re

HANDLE = re.compile(r"^[a-z0-9._]{1,30}$")


def load_world(world_dir):
    path = os.path.join(world_dir, "world.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def assign_role(roles, counts):
    """Pick the role furthest below its quota and bump its count. `counts` is mutated."""
    total = sum(counts.get(r["id"], 0) for r in roles) + 1
    best, gap = roles[0]["id"], float("-inf")
    for r in roles:
        g = r["quota"] * total - counts.get(r["id"], 0)
        if g > gap:
            best, gap = r["id"], g
    counts[best] = counts.get(best, 0) + 1
    return best


def look_seed(handle):
    """FNV-1a 32-bit hash of the handle: a stable seed for hair, skin and clothes."""
    h = 2166136261
    for ch in handle:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def normalize_handle(s):
    """'@Some.User ' -> 'some.user', or None if it is not a valid handle."""
    u = str(s or "").strip().lstrip("@").lower()
    return u if HANDLE.match(u) else None
