# Development

## Project layout

- `data/story.json`: characters, dialogue, links, choice effects and stat requirements.
- `scripts/story_state.gd`: pure story navigation and versioned save validation.
- `scripts/main.gd`: title, dialogue, choices, settings, journal and screenshot capture.
- `scripts/animated_character.gd`: actual 64-frame atlas playback for every outfit.
- `data/wardrobe.json` and `scripts/wardrobe.gd`: clothing catalog and validated per-character selections.
- `scripts/audio_director.gd`: independent music, effects and narration buses.
- `tools/build_assets.py`: deterministic frame and original audio generation.
- `tools/generate_voices.py`: resumable neural narration.
- `tools/validate_assets.py`: transparent, unique frames and verified narration.

## Local checks

```sh
python tools/validate_assets.py
godot --headless --path . --editor --import
godot --headless --path . --script tests/story_test.gd
godot --headless --path . --script tests/runtime_test.gd
godot --path . -- --capture
godot --headless --path . --export-pack Linux build/jade-vow.pck
```

Capture mode writes six actual viewport screenshots to `build/screenshots` and exits. `python tools/verify_screenshots.py` validates them and creates compact JPEG previews. Captures cover the title, dialogue, original wardrobe, training wardrobe, festival wardrobe, and festival clothing in dialogue.
The packaged executable discovers `jade-vow.pck` beside it.

## Story schema

Every node has `speaker`, `actor`, and `text`. It also has exactly one of `next`, `choices`, or `ending`. Choices have `text`, `next`, optional additive `effects`, and optional minimum-stat `requires`. Animations may be `idle`, `wind`, `channeling`, or `resolve`. Named sound effects are optional.

Choices apply effects only when their requirements are met. Failed loads never replace the current journey. Saves are versioned and stored in Godot's `user://` directory; settings use a separate config file.

## Asset accounting

There are 48 atlas PNGs, each an 8×8 grid of 192×512 RGBA cells. Four adult characters each have three outfits and four cycles of 64 frames, totalling 3,072. Their source is twelve portraits in three GPT-generated cast images. CI checks every decoded cell for a globally unique pixel hash, source hashes, the clothing catalog hash, and each atlas hash against the versioned manifest. See [Wardrobe](WARDROBE.md) for clothing persistence and filenames.

Asset baking is resumable: unchanged, verified atlases are reused. The feature-branch bundle job publishes assets and screenshots when media changes or captures are missing; repeat validation keeps the existing media commit intact.

## Scope

This is the first complete short chapter. Longer chapters, additional voices, hand-authored facial rigs, and lip sync can be added through the existing story and asset structure. The current narrator uses one neural timbre with different pacing, and portrait animation uses deformation rather than separate drawn poses.
