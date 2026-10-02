# Development

## Project layout

- `data/story.json`: characters, dialogue, links, choice effects, and stat requirements.
- `scripts/story_state.gd`: story navigation and versioned save validation.
- `scripts/main.gd`: title, dialogue, choices, settings, journal, and viewport capture.
- `scripts/animated_character.gd`: 64-frame atlas playback for every outfit.
- `data/wardrobe.json` and `scripts/wardrobe.gd`: catalog and persistent character selections.
- `data/animation_rigs.json`: source-image hand, elbow, shoulder, face, and hip landmarks.
- `scripts/audio_director.gd`: music, effects, narration buses, and orderly shutdown.
- `tools/build_assets.py`: asset orchestration and original audio synthesis.
- `tools/animation_baker.py` and `tools/pose_rig.py`: pose extraction and articulated cutout animation.
- `tools/animation_motion.py`: translation-aligned opaque-body and silhouette measurements.
- `tools/preview_animations.py`: atlas GIFs, frame comparisons, and rig guides.
- `tools/generate_voices.py`: resumable neural narration.
- `tools/validate_assets.py`: decoded-frame motion, uniqueness, source integrity, and narration checks.

## Local checks

Use Python 3.12 and Godot 4.7.2. Install `requirements.txt`, then run:

```sh
python -m unittest discover -s tests -p 'test_animation_*.py'
python tools/build_assets.py
python tools/generate_voices.py
python tools/validate_assets.py
python tools/preview_animations.py
godot --headless --path . --editor --import
godot --headless --path . --script tests/story_test.gd
godot --headless --path . --script tests/runtime_test.gd
godot --path . -- --capture
python tools/verify_screenshots.py
godot --headless --path . --export-pack Linux build/jade-vow.pck
```

Capture mode writes six viewport screenshots to `build/screenshots` and sixteen timed viewport frames to `build/animations/rendered`. Screenshot verification creates compact JPEG previews, `rendered_game.gif`, and a sampled game-frame sheet. Timed capture fixes the character's initial frame and disables atmospheric background animation so that measured changes reflect the character.

The packaged executable discovers `jade-vow.pck` beside it. CI uses Xvfb with dummy audio for desktop capture and standalone playback. It runs the exported package from a folder without the source checkout and checks logs for errors, missing resources, and clean shutdown.

## Story schema

Each node has `speaker`, `actor`, and `text`, plus exactly one of `next`, `choices`, or `ending`. Choices have `text`, `next`, optional additive `effects`, and optional minimum-stat `requires`. Animations may be `idle`, `wind`, `channeling`, or `resolve`. Named sound effects are optional.

Choices apply effects only when their requirements are met. Failed loads preserve the current journey. Versioned saves live in Godot's `user://` directory; settings use a separate config file.

## Asset accounting and regression checks

There are 48 atlas PNGs, each an 8×8 grid of 384×512 cells: four adult characters × three outfits × four 64-frame loops = 3,072 frames. Their source is 24 GPT key poses in three pose sheets. Separate outfit references and a mountain environment are also GPT-generated.

The 14 Python regression tests cover motion false positives and arm/palm rendering: identical portraits, tiny sway, the old wind/breathing deformation, pans, tint, particles, intermediate-hand opacity, stable body detail, segment transforms, curved hand paths, and minimum travel. Asset validation checks actual decoded atlas frames, all source/code hashes, opaque-body and silhouette movement, palm travel and coverage, and global uniqueness.

Godot runtime tests compare loaded frame textures for all 48 loops and exercise actual playback, wardrobe selection, settings persistence, reduced motion, story progress, and corrupt-config recovery. Story tests traverse every reachable scene and all three endings.

See [Wardrobe](WARDROBE.md) for precise thresholds and persistent settings. `build/animations/motion_report.json` records measured movement and palm coverage for each loop.

Asset baking resumes unchanged, verified atlases. The feature-branch bundle job publishes generated assets and review media in a separate commit, and exits without another commit when assets are unchanged and captures exist.

## Scope

This is a complete short opening. Narration uses one neural timbre with character pacing. Articulated arm gestures, head tilt, hair, and clothing movement are computed from GPT key poses; facial expressions and lip sync are not rigged. Additional chapters, voices, poses, and facial rigs can extend the existing data and asset pipeline.
