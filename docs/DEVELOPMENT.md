# Development

## Project layout

- `data/story.json`: characters, dialogue, links, choice effects, and stat requirements.
- `scripts/story_state.gd`: story navigation, shared choice preview/application validation, and versioned saves.
- `scripts/attributes.gd`: attribute meanings, growth hints, and derived ranks.
- `scripts/main.gd`: title, dialogue, choices, settings, journal, and viewport capture.
- `scripts/animated_character.gd`: intact outfit portraits with runtime body bobbing.
- `data/wardrobe.json` and `scripts/wardrobe.gd`: catalog and persistent character selections.
- `scripts/audio_director.gd`: music, effects, narration buses, and orderly shutdown.
- `tools/build_assets.py`: asset orchestration and original audio synthesis.
- `tools/animation_baker.py`: copy independent native portraits without resampling.
- `tools/preview_animations.py`: body bob WebP previews and portrait contact sheets.
- `tools/generate_voices.py`: resumable neural narration.
- `tools/validate_assets.py`: portrait inventory, transparency, source integrity, and narration checks.

## Local checks

Use Python 3.12 and Godot 4.7.2. `tools/bootstrap_godot.py` pins the official release archive SHA-256 and verifies cached downloads without querying the GitHub API. Install `requirements.txt`, then run:

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

Capture mode writes sixty-six viewport screenshots to `build/screenshots` and sixteen timed viewport frames to `build/animations/rendered`. Screenshot verification creates compact JPEG previews, `rendered_game.webp`, and a sampled game-frame sheet. Timed capture fixes the character's initial frame and disables atmospheric background animation so that measured changes reflect the character.

The packaged executable discovers `jade-vow.pck` beside it. CI uses Xvfb with dummy audio for desktop capture and standalone playback. It runs the exported package from a folder without the source checkout and checks logs for errors, missing resources, and clean shutdown.

## Story schema

Each node has `speaker`, `actor`, and `text`, plus exactly one of `next`, `choices`, or `ending`. Optional `chapter` and `background` select chapter labels and catalog art. Optional `effect` selects `lanterns`, `rain`, `reed_light`, `bell`, `qi`, the three earned trace paintings, `storm_discharge`, or `none`. An `ending` may also have `continuation` to lead into the next book while keeping the ending discoverable. Choices have `text`, `next`, optional additive `effects`, and optional minimum-stat `requires`. Animations may be `idle`, `wind`, `channeling`, or `resolve`. Named sound effects are optional.

The Attributes panel (C) derives ranks from the existing four saved scores at thresholds 0, 3, 6, and 10. The catalog includes descriptions and growth hints; the final rank is descriptive and does not limit points. Choice summaries show additive effects and current/required values in catalog order. `choice_details()` validates destinations, integer requirements, and in-range resulting scores; both `can_choose()` and `choose()` use this validation so the preview matches application. Malformed choices fail before any score, scene, or journal mutation.

A node marked `random_event: true` has two or more distinct `choices` as possible conditions; those alternatives cannot have effects or requirements. The UI exposes Continue instead of selectable cards. `StoryState.advance()` uses a per-journey seed and scene ID; the resolved destination is recorded. Version-1 saves add optional `journey_seed` and `encounters` together, preserving old saved stat keys and scores. Tests cover future outcomes, resolved revisits, seed diversity and atomic invalid-save rejection.

Choices apply effects only when their requirements are met. Failed loads preserve the current journey. Versioned saves live in Godot's `user://` directory; settings use a separate config file.

## Asset accounting and regression checks

There are twelve native 1024×1536 RGBA portrait PNGs: four adult characters × three outfits. Each is an independently generated complete portrait copied byte for byte from its retained master. Godot translates the complete Sprite2D vertically in a four-second loop; the motion label selects a 6–10 pixel bob. The original mountain environment is retained; legacy outfit sheets have been removed.

The portrait regression tests cover byte-preserving generation, reuse and rejection of invalid native masters. Two installer tests check offline reuse of a verified cache and rejection of modified archive bytes. Asset validation checks all twelve decoded portraits, transparency, source/code hashes, audio integrity, and narration coverage. It rejects leftover frame atlases.

Godot runtime tests exercise all 48 outfit/motion combinations, verifying up/down movement, a smooth loop, an unchanged portrait texture, and a still body with reduced motion. They also exercise actual playback, wardrobe selection, settings persistence, story progress, and corrupt-config recovery. Story tests traverse every reachable scene and every authored ending.

See [Wardrobe](WARDROBE.md) for bob settings and persistent outfit choices.

Portrait preparation reuses unchanged, verified files. The feature-branch bundle job publishes generated assets and review media in a separate commit, and exits without another commit when assets are unchanged and captures exist.

## World and manuscript checks

`data/world_assets.json` registers native painted backgrounds, NPCs, spirit beasts, and inspectable items. Item painting inspection does not implement inventory ownership. World portraits render through the same intact-body animation component. The world validator rejects missing or duplicated files, dimensions that disagree with the catalog, sprites without alpha, broken links, unknown cast references, and unreachable scenes. Its JSON report states the authored word count and whether the final production targets have been reached. The present draft has not reached those targets.

Reading scenes use a 680-pixel portrait height with room for the whole bob beneath the navigation bar and above the footer. Title portraits use 730 pixels; wardrobe previews use 350. Uniform scaling preserves proportions. Changing `display_height` updates a cached portrait's scale immediately.

The stateful Godot route traversal includes continuations across all nine books and all authored endings. Test travelers reuse one parsed campaign. With nonnegative stat effects, values at or above the greatest gate are equivalent for reachability; capped states are deduplicated. Overflow and corrupt saves are checked separately at full values. The default `StoryState.new()` still parses its own story, keeping mutated corruption fixtures isolated.

`data/continuity.json` must list every delivered chapter as reviewed and keep its fact anchors valid. Its checkpoints name scenes that must lie on every path to a later decision. The validator removes each required scene in turn and rejects a still-reachable decision, catching shortcuts that bypass knowledge or safety work. Editorial review also covers chronology, custody, privacy, and alternate world outcomes.

Scene effects draw at the current control size. Panels pause their clock; reduced motion removes them immediately. The capture harness re-enables effects after the isolated body-bob recording, so river screenshots show actual rain while motion measurements remain focused on the actor.

## Scope

This draft continues through Book IX; its exact authored count remains far below the requested million-word target. Narration uses one neural timbre with character pacing. Animation is a gentle whole-body bob of each intact portrait. Additional chapters, voices, and outfit portraits can extend the existing data and asset pipeline.

## Extra interior collection

The 100 additional interior paintings are registered as backgrounds with `environment: interior` and `collection: building_interiors`. They do not count toward the original 100-background quota. The total background target is 200. World → Interiors loads one original painting at a time and preserves its aspect ratio. Runtime validation visits every delivered interior and checks caption synchronization, dimensions, invalid selection handling, and selection after the panel is closed. The standalone package also loads the last interior.

Use `python tools/validate_world.py --require-complete` for the production acceptance check, or dispatch Godot CI with `require_complete: true`. Draft validation still checks delivered content without treating unfinished quotas as satisfied. The strict command writes its report before returning failure. PR checks automatically require completeness when the PR leaves draft; ready-for-review and converted-to-draft events trigger new checks. Both modes reject exact repeated scene prose.

## Full-production sprite acceptance

The current target is 500 human NPC originals and 501 spirit-beast originals, preserved independently from the 100 original backgrounds and 100 extra interiors. Every sprite records its retained original source, native dimensions, and creation record. The minimum native detail is 1024×1536 (either orientation); do not upscale to pass it. Decoded painting fingerprints ignore encoding metadata, hidden RGB, and transparent canvas padding. A shared original source cannot count twice. Editorial design review remains necessary to exclude pose, costume, mirror, and recolor derivatives.

Book IV extends every river ending, retains scores and journal history, and adds four orchard settlements. The capture harness visits Ren Qiao, the Frostroot Hart, and the final orchard choice; the standalone package loads both native portraits and their narration.

## Compact media storage

Historical source paintings use lossless WebP with exact RGBA pixels and native dimensions recorded in `assets/art/compression.json`. Bundled narration uses 16000 Hz mono Vorbis quality 0; the manifest records text hashes, decoded timing, and previous file hashes and encodings. Review screenshots use the existing full-size JPEG captures. CI retains this encoding for new narration and bundles JPEG screenshots.

The new core masters and Thunderfen originals retain their native PNG bytes. Do not run compression over catalogued originals without updating source paths, provenance and checksums together. Narration generation already emits compact Vorbis clips. Validate all decoded assets before committing.

Git history was compacted by removing binary media from old commits and retaining optimized media at each branch tip. Earlier source commits remain, but their removed media requires regeneration or recovery from the original bundle. Collaborators should clone the rewritten repository again.
