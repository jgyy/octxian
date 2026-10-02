# Wardrobe assets

`data/wardrobe.json` is the shared catalog for portrait preparation and Godot wardrobe controls. Each outfit has an ID, display name, description, reference artwork, and a GPT pose sheet. The catalog also sets the four-second bob period and a 6–10 pixel vertical amplitude for each story motion label.

## Intact portraits

`tools/animation_baker.py` selects the complete resting drawing from the top row of each pose sheet. It separates rows at their transparent seam, crops transparent margins, preserves the drawing's proportions, and centers it in a transparent **384×512** image.

The twelve generated portraits use names such as `lin_yue.png`, `lin_yue_training.png`, and `lin_yue_festival.png`. The manifest records source, catalog, builder-code, and output SHA-256 hashes. Unchanged portraits are reused. Run `python tools/build_assets.py --force` to regenerate every appearance.

## Playback and persistence

`scripts/animated_character.gd` loads one complete portrait into a Sprite2D. It smoothly moves the whole sprite vertically with a sine wave. The `idle`, `channeling`, `wind`, and `resolve` labels select the bob amplitude. The drawing remains intact throughout the loop. Gallery previews use the same motion, scaled to their display height.

Reduced motion resets the sprite to its resting position and stops bobbing. Changing an outfit resets the cycle. The character uses the reference artwork as a fallback if its generated portrait is unavailable.

`scripts/wardrobe.gd` validates choices and restores defaults for invalid saved values. Selections are saved in `wardrobe/choices` in Godot's `user://settings.cfg`, independently of story saves. Each character's wardrobe persists across journeys and sessions.

## Validation and previews

Python tests check resting-pose selection, preserved proportions, and missing artwork. Asset validation verifies all twelve portrait hashes, dimensions, transparency, audio, and narration, and rejects obsolete frame atlases.

Godot tests exercise all 48 character/outfit/motion combinations. They check up/down movement, a smooth loop, an unchanged portrait texture, actual playback, and a still body with reduced motion enabled. They also cover wardrobe dropdowns and saved choices.

`tools/preview_animations.py` creates bob GIFs and contact sheets from the same portraits and catalog settings. Timed Godot captures verify movement in the running game with background motion disabled. CI publishes these under `docs/animations` and captures all three wardrobes plus selected clothing in a story scene.
