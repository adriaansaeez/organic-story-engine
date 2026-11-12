#!/usr/bin/env bash
# Rebuild a world's generated assets and copy the kit into an episode project.
#
#   engine/tools/sync_world.sh examples/village/world my-series/ep01
#
# Writes <episode>/kit/ (runtime + sprites + fog + maps + scenes) and, when the
# episode has a sound.json, rebuilds <episode>/assets/audio/ambience.wav.
# Never edit files under kit/: edit the world or the engine and sync again.
set -euo pipefail
ENGINE="$(cd "$(dirname "$0")/.." && pwd)"
WORLD="$(cd "${1:?world dir}" && pwd)"
EP="$(cd "${2:?episode dir}" && pwd)"

python3 "$ENGINE/tools/sprites.py" --world "$WORLD"
python3 "$ENGINE/tools/fog.py" --world "$WORLD"
python3 "$ENGINE/tools/scenes.py" --world "$WORLD"

KIT="$EP/kit"
mkdir -p "$KIT/lib" "$KIT/assets/sprites" "$KIT/assets/fx" "$KIT/assets/maps" "$KIT/assets/scenes" "$EP/assets/audio"
cp "$WORLD"/assets/sprites/*.png "$WORLD/assets/sprites/manifest.js" "$KIT/assets/sprites/"
cp "$WORLD"/assets/fx/*.png "$KIT/assets/fx/"
cp "$WORLD"/assets/maps/*.png "$WORLD"/assets/maps/*.js "$KIT/assets/maps/"
if compgen -G "$WORLD/assets/scenes/*.png" > /dev/null; then cp "$WORLD"/assets/scenes/*.png "$KIT/assets/scenes/"; fi
if [ -d "$WORLD/assets/landmarks" ]; then mkdir -p "$KIT/assets/landmarks" && cp "$WORLD"/assets/landmarks/*.png "$KIT/assets/landmarks/"; fi
cp "$ENGINE/runtime/story.js" "$ENGINE/runtime/story.css" "$KIT/lib/"

if [ -f "$EP/sound.json" ]; then
  python3 "$ENGINE/tools/sfx.py" "$EP/sound.json" "$EP/assets/audio/ambience.wav"
fi
echo "kit synced -> $KIT"
