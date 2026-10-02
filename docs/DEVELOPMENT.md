# Development

## Project layout

- `data/story.json`: characters, dialogue, links, choice effects, and stat requirements.
- `scripts/story_state.gd`: story navigation and versioned save validation.
- `scripts/main.gd`: title, dialogue, choices, settings, journal, and viewport capture.
- `scripts/animated_character.gd`: intact outfit portraits with runtime body bobbing.
- `data/wardrobe.json` and `scripts/wardrobe.gd`: catalog and persistent character selections.
- `scripts/audio_director.gd`: music, effects, narration buses, and orderly shutdown.
- `tools/build_assets.py`: asset orchestration and original audio synthesis.
- `tools/animation_baker.py`: extract complete resting portraits without stretching.
- `tools/preview_animations.py`: body bob GIFs and portrait contact sheets.
- `tools/generate_voices.py`: resumable neural narration.
- `tools/validate_assets.py`: portrait inventory, transparency, source integrity, and narration checks.

## Local checks

Use Python 3.12 and Godot 4.7.2. Install `requirements.txt`, then run:

```sh
python -m unittest discover -s tests -p 'test_*.py'
python tools/build_assets.py
python tools/generate_voices.py
python tools/validate_assets.py
python tools/validate_world.py
python tools/preview_animations.py
godot --headless --path . --editor --import
godot --headless --path . --script tests/story_test.gd
godot --headless --path . --script tests/runtime_test.gd
godot --path . -- --capture
python tools/verify_screenshots.py
godot --headless --path . --export-pack Linux build/jade-vow.pck
```

Capture mode writes eleven viewport screenshots to `build/screenshots` and sixteen timed viewport frames to `build/animations/rendered`. Screenshot verification creates compact JPEG previews, `rendered_game.gif`, and a sampled game-frame sheet. Timed capture fixes the character's initial frame and disables atmospheric background animation so that measured changes reflect the character.

The packaged executable discovers `jade-vow.pck` beside it. CI uses Xvfb with dummy audio for desktop capture and standalone playback. It runs the exported package from a folder without the source checkout and checks logs for errors, missing resources, and clean shutdown.

## Story schema

Each node has `speaker`, `actor`, and `text`, plus exactly one of `next`, `choices`, or `ending`. Optional `chapter` and `background` select chapter labels and catalog art. An `ending` may also have `continuation` to lead into the next book while keeping the ending discoverable. Choices have `text`, `next`, optional additive `effects`, and optional minimum-stat `requires`. Animations may be `idle`, `wind`, `channeling`, or `resolve`. Named sound effects are optional.

Choices apply effects only when their requirements are met. Failed loads preserve the current journey. Versioned saves live in Godot's `user://` directory; settings use a separate config file.

## Asset accounting and regression checks

There are twelve 384×512 portrait PNGs: four adult characters × three outfits. Each is an intact resting pose from the top row of its GPT pose sheet. Godot translates the complete Sprite2D vertically in a four-second loop; the motion label selects a 6–10 pixel bob. Separate outfit references and a mountain environment are also GPT-generated.

The three Python regression tests cover selection of the intact resting pose, preserved aspect ratio, and missing artwork. Asset validation checks all twelve decoded portraits, transparency, source/code hashes, audio integrity, and narration coverage. It rejects leftover frame atlases.

Godot runtime tests exercise all 48 outfit/motion combinations, verifying up/down movement, a smooth loop, an unchanged portrait texture, and a still body with reduced motion. They also exercise actual playback, wardrobe selection, settings persistence, story progress, and corrupt-config recovery. Story tests traverse every reachable scene and all three endings.

See [Wardrobe](WARDROBE.md) for bob settings and persistent outfit choices.

Portrait preparation reuses unchanged, verified files. The feature-branch bundle job publishes generated assets and review media in a separate commit, and exits without another commit when assets are unchanged and captures exist.

## World and manuscript checks

`data/world_assets.json` registers native painted backgrounds, NPCs, and spirit beasts. World portraits render through the same intact-body animation component. The world validator rejects missing or duplicated files, dimensions that disagree with the catalog, sprites without alpha, broken links, unknown cast references, and unreachable scenes. Its JSON report states the authored word count and whether the final production targets have been reached. The present draft has not reached those targets.

Reading scenes use a 680-pixel portrait height with room for the whole bob beneath the navigation bar and above the footer. Title portraits use 730 pixels; wardrobe previews use 350. Uniform scaling preserves proportions. Changing `display_height` updates a cached portrait's scale immediately.

The stateful Godot route traversal includes Book I continuations and all seven endings. Repeated `(scene, stats)` states are deduplicated so converging routes do not inflate work or manuscript counts.

## Scope

This draft extends the complete short opening with Book II. Narration uses one neural timbre with character pacing. Animation is a gentle whole-body bob of each intact portrait. Additional chapters, voices, and outfit portraits can extend the existing data and asset pipeline.
