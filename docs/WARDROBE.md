# Wardrobe assets

`data/wardrobe.json` maps four adult characters and three outfits to twelve independent `assets/art/core/*.png` originals. Every master is a native **1024×1536 RGBA** tool output. The former cast sheets, pose sheets and 384×512 derived portraits have been removed. [Creation records](../assets/art/CORE_PROVENANCE.md) identify all replacements.

## Native portrait preparation

`tools/animation_baker.py` verifies native dimensions and alpha, then copies each source byte for byte to `assets/generated/sprites/`. It does not crop, resize, pad or flatten the original. Manifest version 5 records the master path, native size, identical source/output SHA-256, catalog hash and builder-code hash. Verified unchanged files are reused; `python tools/build_assets.py --force` refreshes every appearance.

## Playback and persistence

`scripts/animated_character.gd` loads a complete portrait into Sprite2D. Godot moves the whole sprite vertically with a four-second sine loop; `idle`, `channeling`, `wind` and `resolve` select 6–10 pixel amplitudes. Display scaling preserves proportions. Reduced motion restores the resting position; panels pause the loop. The fallback uses the same individual native source.

Wardrobe choices are independently validated and stored in `wardrobe/choices` in `user://settings.cfg`. Clothing persists across journeys without changing story scores. Invalid saved selections restore defaults.

## Validation and previews

Python tests check byte-preserving generation, reuse, and rejection of low-resolution, flattened, empty or opaque masters. Asset validation checks all twelve source/output hashes, dimensions, alpha, narration and audio. Godot tests exercise all 48 character/outfit/motion combinations, smooth whole-body movement, unchanged textures, reduced motion, dropdowns and persistence.

`tools/preview_animations.py` creates compact review previews from the originals. Timed Godot viewport captures disable atmosphere while measuring body movement. These review exports are display previews; runtime portraits retain their complete native bytes. CI bundles screenshots and previews under `docs/` after successful validation.
