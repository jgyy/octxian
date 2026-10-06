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

Capture mode writes eighty-three viewport screenshots to `build/screenshots` and sixteen timed viewport frames to `build/animations/rendered`. Screenshot verification creates compact JPEG previews, `rendered_game.webp`, and a sampled game-frame sheet. Timed capture fixes the character's initial frame and disables atmospheric background animation so that measured changes reflect the character.

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

The stateful Godot route traversal includes continuations across all eighteen books and all authored endings. Test travelers reuse one parsed campaign. With nonnegative stat effects, values at or above the greatest gate are equivalent for reachability; capped states are deduplicated. Overflow and corrupt saves are checked separately at full values. The default `StoryState.new()` still parses its own story, keeping mutated corruption fixtures isolated.

`data/continuity.json` must list every delivered chapter as reviewed and keep its fact anchors valid. Its checkpoints name scenes that must lie on every path to a later decision. The validator removes each required scene in turn and rejects a still-reachable decision, catching shortcuts that bypass knowledge or safety work. Editorial review also covers chronology, custody, privacy, and alternate world outcomes.

Scene effects draw at the current control size. Panels pause their clock; reduced motion removes them immediately. The capture harness re-enables effects after the isolated body-bob recording, so river screenshots show actual rain while motion measurements remain focused on the actor.

## Scope

This draft continues through Book XVIII with 1,154,076 displayed prose words. The manuscript requires 845,924 additional displayed words to reach the 2,000,000-word target; the independent artwork quotas remain incomplete. Narration uses one neural timbre with character pacing. Animation is a gentle whole-body bob of each intact portrait. Additional chapters, voices, and outfit portraits can extend the existing data and asset pipeline.

## Extra interior collection

The 100 additional interior paintings are registered as backgrounds with `environment: interior` and `collection: building_interiors`. They do not count toward the original 100-background quota. The total background target is 200. World → Interiors loads one original painting at a time and preserves its aspect ratio. Runtime validation visits every delivered interior and checks caption synchronization, dimensions, invalid selection handling, and selection after the panel is closed. The standalone package also loads the last interior.

Use `python tools/validate_world.py --require-complete` for the production acceptance check, or dispatch Godot CI with `require_complete: true`. Draft validation still checks delivered content without treating unfinished quotas as satisfied. The strict command writes its report before returning failure. PR checks automatically require completeness when the PR leaves draft; ready-for-review and converted-to-draft events trigger new checks. Both modes reject exact repeated scene prose.

## Full-production sprite acceptance

The current target is 500 human NPC originals and 501 spirit-beast originals, preserved independently from the 100 original backgrounds and 100 extra interiors. Every sprite records its retained original source, native dimensions, and creation record. The minimum native detail is 1024×1536 (either orientation); do not upscale to pass it. Decoded painting fingerprints ignore encoding metadata, hidden RGB, and transparent canvas padding. A shared original source cannot count twice. Editorial design review remains necessary to exclude pose, costume, mirror, and recolor derivatives.

Book IV extends every river ending, retains scores and journal history, and adds four orchard settlements. The capture harness visits Ren Qiao, the Frostroot Hart, and the final orchard choice; the standalone package loads both native portraits and their narration.

## Compact media storage

Historical source paintings use lossless WebP with exact RGBA pixels and native dimensions recorded in `assets/art/compression.json`. Bundled narration uses 8000 Hz mono Vorbis constrained to 10000 bit/s; the manifest records text hashes, decoded timing, and previous file hashes and encodings. Review screenshots use the existing full-size JPEG captures. CI retains this encoding for new narration and bundles JPEG screenshots.

The new core masters and Thunderfen originals retain their native PNG bytes. Do not run compression over catalogued originals without updating source paths, provenance and checksums together. Narration generation emits the same compact Vorbis setting. Recompress voices alone with `python tools/optimize_assets.py --voices-only --workers 6`. This reduces audio fidelity to a 4 kHz speech bandwidth while retaining complete clips, timing and text hashes. All conversions are decoded and staged before the original voice folder is replaced. Validate all decoded assets before committing.

Git history was compacted by removing binary media from old commits and retaining optimized media at each branch tip. Earlier source commits remain, but their removed media requires regeneration or recovery from the original bundle. Collaborators should clone rewritten `main` with `git clone --single-branch --branch main git@github.com:jgyy/octxian.git`. Other remote branches retain their earlier history; fetching them will restore the old media objects. The compact checkout tracks only `main`.

## Storm and salt-road continuation

Books X and XI continue all three prior endings while keeping the earned fourth stage. The source audits identify 53 distinct existing-content defects, with 78 exact current anchors and an original-node index. Run `python tools/validate_continuation_audits.py --source-base d2ce2851c8e47842104607ec5999ffba6fdabe1c --source-node-index docs/CONTINUATION_SOURCE_INDEX_20261003.json`. CI runs this validator alongside regression tests and adds six actual captures, bringing the total to 72. The source-free smoke test loads both new chapters, their two portrait originals, native environment dimensions and generated Vorbis narration. [Current scope and accounting](CONTINUATION_20261003.md).

## Million-word integration

Books XII–XVII now load through the campaign manifest. Run `python -m tools.validate_million_continuation --verify-source` with source commit cc4bb2d558bcdb7deae656a76ae07abde30f7a6b available. CI fetches that exact source and authenticates 101 choice/transition anchors. It reuses the prior branch's draft narration only after validating every clip against its actual playable text.

Run `godot --headless --path . --script tests/continuation_test.gd` for once-only practice credit, saved completion records, invalid-save atomicity, all five late-role choices, ensemble portrait bounds and layered-motion behavior. New viewport captures are forest_ensemble, lanternwing_crane, desert_attributes, archive_ensemble and archive_courtyard and archive_lantern_keeper. The feature-branch bundle publishes tested media after the full game job succeeds.

The route traversal now retains nondominated capped score vectors at each scene. Because requirements are minima and effects are nonnegative, a stronger vector can take every choice of a weaker one. The source validator also verifies that the campaign is acyclic, making once-only completion history irrelevant to future route availability. This preserves scene and ending coverage while avoiding repeated traversal of the million-word campaign for weaker score variants. Exact saves, score overflow and corrupt input remain separate engine regressions.

Full CI sets `JADE_VOW_VOICE_WORKERS=4` for independent narration clips. Each inference uses one CPU thread; Piper's phonemizer uses its own lock. A single coordinator writes atomic completion checkpoints and validates every clip. Local generation defaults to one worker. The parallel regression forces out-of-order completion and verifies each scene's text hash and the sole checkpoint writer.

The bundle job dispatches CI for its committed media head in a separate concurrency group. It checks matching open PRs and enables strict production quotas when any is no longer draft. That verification run never creates another media commit.

Before the expanded clips are bundled, CI can bootstrap narration from successful integration run [37182354432](https://github.com/jgyy/octxian/actions/runs/37182354432). This optional artifact restore runs only while the first archive closing clip is absent; expired artifacts fall back to generation. Every adopted clip still undergoes model, text, byte and decoded-audio checks. Required validation and package playback remain mandatory.

## Deferred growth and desert dilemmas (2026-10-05)

Run `python -m tools.validate_narrative_revision --verify-source` with fixed source 2b431cb2c113608bb05e1c95edc1ef9b7879d01f fetched locally. It authenticates 101 additional selection/completion repairs, 70 geographic staging corrections and six inserted dilemmas. The six decisions add eighteen distinct consequences while retaining the original next observations and at least two ungated routes each.

Run `godot --headless --path . --script tests/narrative_revision_test.gd` to exercise every deferred branch, new and migrated checkpoints, duplicate-credit prevention and all dilemma outcomes. New version-1 saves use `practice_rules: 1`; earlier saves recognise already-paid growth from their journal and exclusive current branch without changing scores.

Five real captures show the Bitter Wells yard, workroom, lodging, a harder dilemma and completed comparison credit. Native art and proof records are linked in [the narrative review](NARRATIVE_REVISION_20261005.md). The original-picture files remain their independently returned 1536×1024 PNG bytes.

## Storm and salt-road completion credit (2026-10-06)

Run `python -m tools.validate_storm_salt_repairs --verify-source` with fixed source `c90102c720c0fd97fe31559851c57ee38e976d55` available. The audit authenticates thirteen additional selection/completion sites. Run `godot --headless --path . --script tests/storm_salt_repairs_test.gd` for rules 0–3, pending and completed saves, continued endings, overflow, duplicate credit and atomic rejection of unsupported revisions.

New saves retain version 1 and use `practice_rules: 3`. Revision-2 checkpoints recognize credit actually paid on the newly deferred thirteen branches; pending work from the two earlier causality revisions stays pending. Two new real viewport captures show storm household completion and the seed-lot trial's completion. No displayed text or art was changed; the manuscript total remains 1,154,076.

## Saved choices and Book XVIII (2026-10-06)

The campaign contains 1,154,076 displayed words in 13,079 scenes and 18 books; 845,924 remain for two million. The source audit distinguishes one pre-existing inconsistent fact from six missing-followthrough improvements. It does not claim 1,000 literary repairs.

Run `python -m tools.validate_consequence_revision --verify-source` with source commit `3530d7283d0f326771b8f3661c173ad222591898` available. The validator authenticates the original repair, six original decisions and unchanged fallback passages, exclusive callbacks and baseline scan counts. The world validator follows actual recorded-choice conditions, rather than accepting an impossible union of their edges.

Run `godot --headless --path . --script tests/consequences_test.gd` for engine save, revisit and atomic-rejection fixtures and `tests/authored_consequences_test.gd` for real authored decision/save/routing contracts. The complete route test retains future-relevant decisions and checks reachable attribute gates. Four new actual capture names are consequence_choices, consequence_house, consequence_school and consequence_lamp. Their three delayed results come from real selected-path walks at identical attributes.
