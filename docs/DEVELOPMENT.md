# Development

## Project layout

- `data/story.json` contains the campaign root, shared definitions and the ordered book manifest. `tools/story_data.py` and `scripts/story_data.gd` merge each fragment once and reject conflicting IDs or missing files.
- `data/books/` holds independently authored book fragments. Each fragment has exactly `chapters`, `characters` and `nodes` objects.
- `scripts/story_state.gd` handles navigation, atomic choice validation, actual decision records, completed practice and versioned saves.
- `scripts/main.gd` displays the title, dialogue, choices, settings and journal and runs viewport captures and package smoke checks.
- `data/cultivation.json`, `tools/cultivation.py` and `docs/CULTIVATION_PROGRESS.json` define earned cultivation and independently recomputed manuscript credit.
- `data/continuity.json` records reviewed chapters, anchored facts and checkpoints that cannot be bypassed.
- `data/world_assets.json` registers original backgrounds, NPCs, beasts, objects and effects.
- `scripts/animated_character.gd`, `data/wardrobe.json` and `scripts/wardrobe.gd` retain complete original portraits and saved outfit choices.
- `scripts/audio_director.gd` manages music, effects and narration; `tools/generate_voices.py` validates and resumes neural speech generation.
- `tools/verify_screenshots.py` checks actual viewport captures and timed portrait animation. `docs/content_report.json` is the latest measured bundle report.

## Current campaign

The manifest loads **23 books**, **24,341 scenes** and **2,080,062 displayed prose words**. The two-million-word target is met. Word counts include playable alternatives and exclude labels, choice text, prompts and documentation.

Book XXII provides three approaches to Qiu Lian's instrument trial. Its three retained ending markers now continue into Book XXIII. Book XXIII adds a shared root and **120 path fragments**, twenty for each of six later-season inquiries. All new nodes retain Qi Gathering 5: Four pairs, no new practice credit and the affected shoulder's limits.

[Season counts, accounts, continuity and captures](SEASON_PATHS_20261008.md) · [Rival chapter](RIVAL_PATHS_20261008.md)

The 98 world backgrounds comprise 50 ordinary locations and 48 additional interiors. The draft has 67 human NPC paintings and 15 beasts, giving 82 distinct world sprites. Preserve the original quotas: 100 ordinary backgrounds, 100 additional interiors, 500 human NPCs and 501 beasts. Full artwork and the requested 1,000 authenticated plot repairs remain unfinished, so the PR remains draft.

## Local checks

Use Python 3.12, ffmpeg and Godot 4.7.2. The bootstrap tool pins and checks the official engine archive SHA-256.

```sh
python -m pip install -r requirements.txt
python tools/bootstrap_godot.py
python -m unittest discover -s tests -p 'test_*.py'
python tools/build_assets.py
python tools/validate_world.py
python tools/preview_animations.py
.cache/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --path . --editor --import
.cache/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --path . --script tests/story_test.gd
.cache/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --path . --script tests/runtime_test.gd
.cache/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --path . --script tests/rival_paths_test.gd
.cache/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --path . --script tests/season_paths_test.gd
.cache/godot/Godot_v4.7.2-stable_linux.x86_64 --path . -- --capture
python tools/verify_screenshots.py
python tools/generate_voices.py
python tools/validate_assets.py
.cache/godot/Godot_v4.7.2-stable_linux.x86_64 --headless --path . --export-pack Linux build/jade-vow.pck
```

Fixed-source audit checks also require their pinned commits locally. The [CI workflow](../.github/workflows/ci.yml) fetches every required source and runs all evidence validators and campaign regressions. The harbor catalog follow-up uses source commit `f50979b6bb8e3bbed6eec7b866c92377509a964b`; the rival literary evidence uses `0fe9938bf765611b3fe9d31c747fec6067346620`.

## Navigation and persistence

Each scene has `speaker`, `actor` and `text`, plus exactly one of `next`, `choices` or `ending`. Optional `chapter` and `background` select labels and art. An ending may retain a `continuation` into the next book.

Ordinary choices have `text`, `next`, optional additive `effects` and optional minimum-stat `requires`. Preview and application use the same validation. Invalid choices fail before changing scores, the scene, history or practice. A previously recorded choice permits only its saved destination and applies its effects once. Replaying the matching destination cannot repeat a reward or a negative cost.

A `routes` list on a scene with `next` selects the first matching actual recorded decision and destination. It falls back to `next` when no matching record exists. Scores cannot reconstruct a missing enrollment, refusal, relationship or specialist qualification.

A `random_event: true` scene has distinct possible conditions without effects or requirements. Continue resolves its destination from the saved journey seed and scene ID; resolved encounters remain recorded. Random conditions cannot be used to earn practice repeatedly.

Versioned saves live in Godot's `user://` directory. They preserve scores, full decision history, completed practice, journal and encounter context. Failed loads leave the active journey intact. Settings use a separate configuration file.

Future-decision analysis trims only traversal signatures. Each decision stays relevant until its final downstream gate; save files retain the actual full history. Season checks enumerate every new scene under a possible local choice history, require an acyclic graph and bound simultaneous relevant decisions at four.

## Original artwork and motion

Original PNG bytes and creation records remain under `assets/art/`. Do not substitute resized, padded, cropped, recolored or re-encoded files to satisfy counts. The world validator checks native dimensions, byte/source provenance and visible-pixel uniqueness.

The two rival sprites are original RGBA 1024×1536 PNGs. Seven season backgrounds retain six 1672×941 canvases and one 1659×948 canvas. Three season locations are additional interiors. Their tests verify exact byte counts and Git blob SHA-1, including the Git object header, and require every background to appear in playable prose.

Wardrobe art uses twelve independent native 1024×1536 RGBA portraits: four adult characters with three outfits each. Runtime motion translates the intact portrait vertically in a four-second loop; it does not replace the source with an atlas. Reduced motion keeps the body still. The runtime regressions cover all 48 outfit/motion combinations, preserved texture, smooth loops, settings and saved selections.

[Wardrobe](WARDROBE.md) · [Season provenance](../assets/art/SEASON_20261008_PROVENANCE.md) · [Rival provenance](../assets/art/RIVALS_20261008_PROVENANCE.md)

## Capture, narration and packaging

Capture mode writes **164 actual viewport screenshots** to `build/screenshots` and sixteen timed viewport frames to `build/animations/rendered`. The verifier produces compact JPEG previews, a measured content report, WebP animation and sampled frames only after validation passes.

The fifteen season captures walk actual zero-score routes with save/load checkpoints: the path choice, six entries, six endings, the letter counter and the kiln public room. Captures occur before newly generated narration. Package checks later require the narrated anchors, all seven new native background textures, both rival sprites and real completion of all six season paths.

Piper Lessac supplies neural narration for every displayed scene. Text, bytes and decoded audio are independently checked before reuse; changed prose is regenerated. Speech uses 8 kHz mono Vorbis capped at 10 kb/s to limit downloads. `JADE_VOW_VOICE_WORKERS=4` runs four bounded generation workers; cache and manifest validation remain mandatory. Music and effects are original synthesized audio.

The exported `jade-vow` discovers `jade-vow.pck` beside it. CI launches the package under Xvfb with dummy audio from a folder without the source checkout and checks missing resources, errors and shutdown. Linux artifacts retain the project license, Piper model card and Godot notices.

The feature-branch bundle job retains verified generated assets, review captures and the measured report in a separate commit. It then explicitly dispatches validation of that new head. Draft runs report delivered quotas; `--require-complete` requires every production manuscript and art target.

## Evidence policy

Historical repair reports pin the old source, exact passages and actual contradiction. Book XXII adds two literary roots across three existing passages. Its saved-choice replay correction is a separate engine fix. The He Ming gallery follow-up aligns an asset description with the established female salt-packer role and receives no additional literary root credit.

New events, ordinary callbacks and corrections made before publication do not count as repaired historical plot holes. Anchored continuity facts and checkpoint-removal tests provide useful regression evidence without proving all literary consistency.

[Story authoring](STORY_AUTHORING.md) · [Cultivation canon](CULTIVATION_SYSTEM.md) · [Latest measured report](content_report.json)
