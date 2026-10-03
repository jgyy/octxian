# Jade Vow

[![Godot CI](https://github.com/jgyy/octxian/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/jgyy/octxian/actions/workflows/ci.yml)

An original xianxia visual novel built in **Godot 4.7.2 stable**, the latest stable release verified on 2026-10-02.

Lin Yue begins as a mortal kiln worker with no retained qi. Earn meals, survive failed tests and injury, temper the body, and learn to hold the first measured trace of spiritual energy. Above the lower training terrace floats a mountain whose ancient cultivation array is failing.

![Jade Vow title screen](docs/screenshots/title.jpg)

## Play

Download the `jade-vow-linux` artifact from a successful [CI run](https://github.com/jgyy/octxian/actions/workflows/ci.yml), extract `jade-vow-linux.tar.gz`, and run `./jade-vow`. Keep `jade-vow.pck` beside the executable.

Or clone this repository, open `project.godot` in Godot 4.7.2, and press F6/F5. Generated sprites, music, effects, and neural narration are bundled in the repository.

To run the game from a terminal, install Godot and run these commands from the repository root (`octxian/`):

```sh
# Import the bundled assets on the first run.
godot --headless --path . --editor --import
# Launch the game window.
godot --path .
```

If your Godot executable is named `godot4`, replace `godot` with `godot4` in both commands. After the first import, use `godot --path .` to play again.

- **Enter / Space:** finish the current line, then advance.
- **1–4:** select an available choice.
- **S:** save. **L:** open the dialogue journal. **C:** open attributes. **Esc:** close a panel or open settings.
- The interface provides save/load, auto reading, fast text, an animated wardrobe gallery, audio levels, and reduced motion.

The playable script contains **1,606 scenes and 137,918 authored words** across seven books, with cultivation stats and gated choices. Book I has three endings; each continues into Book II, which has three investigations and four settlements. Every settlement continues into Book III, with three river routes, six settlement approaches, and three endings. Each continues into Book IV's orchard, with three investigations and four settlements. Every orchard outcome continues into Book V, with three city investigations and four resolutions. Each city resolution continues into Book VI, with four investigations, local branch choices and four bounded court remedies. Every court outcome continues into Book VII's three river investigations and three owner-approved arrangements.

This draft expansion currently adds **nine original-scope backgrounds, 32 extra building-interior backgrounds, fifteen human NPC sprites, eight spirit-beast sprites, four inspectable item paintings, and two cultivation effects** at their native generated sizes. The original 100-background quota, 500 human NPCs, 501 spirit beasts and more than one million words remain unfinished. The separate extra 100-interior quota has 32 delivered paintings. Run `python tools/validate_world.py --require-complete` to check all quotas. CI writes exact delivery counts to `build/content_report.json`.

## Cultivation rewrite (draft)

The cultivation rewrite currently delivers **19,805 words across 300 scenes**. The mortal opening contains 77 training scenes and 36 recast Book I scenes; the sluice apprenticeship contains 131 scenes. The whole campaign contains **137,918 displayed words**; 118,113 inherited words still await recast.

The latest [plot-hole review](docs/PLOT_HOLE_REVIEW.md) repairs 45 scenes, including four new mandatory scenes. Common routes now establish the star's terms, the harbor's funded renewal and the missing link in Wei Jin's custody records. Later powers respect the earned first arm pair, finite artifact fuel and ordinary load-bearing tools.

Lin Yue earns Qi Gathering stage two through three calibrated overnight retention trials, then stage three through slow paired-meridian work, a misleading instrument fault, eleven rest days and three recovered examinations. Reserve, throughput, purity, sampling discharge and technique delivery loss are distinct. Reed-Step powers an external conducting stitch through the first arm pair; crews and separate stones carry the larger ward loads.

The [cultivation canon](docs/CULTIVATION_SYSTEM.md) defines twelve gates, anatomy, tests, recovery, techniques, crafts and resources. Open **Attributes → Cultivation realms** for its in-game reference. Choice attribute ranks never award realms.

Ten native generated masters cover two environments, two human NPCs, two monsters, two items and two effects. This continuation adds the **1536×1024 sluice**, **1024×1536 Duan Zhi, brine mantis and caliper**, and **1536×1024 paired trace**. [Provenance](assets/art/CULTIVATION_PROVENANCE.md) records their native dimensions; no enlargement is credited.

The fourteen-volume architecture budgets 1,050,000 original words. The [production ledger](docs/CULTIVATION_REWRITE.md) and [verified scene accounting](docs/CULTIVATION_PROGRESS.json) distinguish delivered rewrite, inherited prose and the **980,196 rewrite words still needed**. The PR remains a draft.

![Mortal recruitment and zero qi](docs/screenshots/mortal_arrival.jpg)

![Cultivation realm reference](docs/screenshots/cultivation_codex.jpg)

![Duan Zhi at the brine sluice](docs/screenshots/sluice_examiner.jpg)

![Earned second-stage retention](docs/screenshots/sluice_retention.jpg)

![Earned first paired meridian route](docs/screenshots/paired_channel.jpg)

![Brine mantis response choices](docs/screenshots/brine_mantis.jpg)

![Bronze meridian caliper inspection](docs/screenshots/object_meridian_caliper.jpg)

## Character attributes

Open **Attributes** in the top navigation, or press **C**, to inspect Lin Yue's **Qi, Trust, Insight, and Resolve**. Each attribute has a description, a growth hint, a rank, and progress toward its next rank. Choices show their point changes before selection, and locked choices show your current and required points. A short confirmation shows the gains after you choose.

Ranks advance at **3, 6, and 10 points**. The highest rank does not cap your points. Story requirements use exact point totals, and attributes persist across books and in existing saves. Beginning a new journey resets all four to zero.

![Character attributes](docs/screenshots/attributes.jpg)

![Visible choice requirements](docs/screenshots/attribute_choices.jpg)

![Branching dialogue](docs/screenshots/dialogue.jpg)

## Book II: The valley that kept its name

Continue from any Book I ending using the **→** continuation button. Su Lan leads you into Salt Lantern Valley, where a protective ward has erased nineteen households from the village register. Investigate the ferry boundary, meet the accused Reed Listener, or examine altered records in the archive. Each investigation offers three approaches, costs, and testimony before a final settlement.

The **World** gallery previews the delivered locations, people, and spirit beasts. The new paintings are preserved at their native sizes: **1672×941** for the five earlier backgrounds, **1024×1536** for each sprite and the clapper, and **1536×1024** for the echo case. Display scaling preserves proportions; no upscaling is presented as added detail. Choose **World → Interiors** for a larger preview of the extra interior paintings; the [interior inventory](docs/INTERIORS.md) records every native file and size.

![Book II quest choices](docs/screenshots/quest_hub.jpg)

![The Reed Listener encounter](docs/screenshots/spirit_encounter.jpg)

![World art gallery](docs/screenshots/world_gallery.jpg)

![Wei Jin at the ferry crossing](docs/screenshots/ferry_encounter.jpg)

![An Ru and the original ledger](docs/screenshots/archive_encounter.jpg)

## Book III: The river without a shore

The next spring, living ferry pilot Wei Xiu charts an empty boat circling a landing lost to a flood. Mo Ran entrusted a copy of one memory to its river keeper eleven years earlier. Negotiate a new return place, survey an accessible replacement stair, or establish a supported harbor. Each route has a second choice with different costs and keeps permission separate for each echo.

Scene effects include rain, reed light, soft bell ripples, and qi motes. Effects pause behind panels and disappear with reduced motion. Open **World → Inspect objects** to examine the clapper and sealed echo case; looking at their paintings does not transfer their custody.

![Wei Xiu at the north landing](docs/screenshots/river_pilot.jpg)

![The Mooring Eel](docs/screenshots/river_spirit.jpg)

![The sheltered reach](docs/screenshots/river_harbor.jpg)

![Sealed echo case inspection](docs/screenshots/object_sealed_echo_case.jpg)

See [the continuity review](docs/CONTINUITY.md) and [the production scope and word budgets](docs/EXPANSION.md) for established facts and remaining work.

## Book IV: The orchard of unfinished winters

Continue from any river ending into the same spring. Ren Qiao's healing orchard transfers temporary sensations while leaving injuries in need of ordinary care. An inherited winter obligation has outlasted the offers that created it. Study the circuit, hear the patients, or examine the accounts before choosing a breathing trial, paid care rota, relief fund, or reviewed pause.

Ren Qiao and the Frostroot Hart have new independent native **1024×1536** portraits. Their native paintings are stored as lossless WebP and checked for transparency, source provenance, and decoded duplicates.

![Ren Qiao in the healing hall](docs/screenshots/orchard_healer.jpg)

![The Frostroot Hart](docs/screenshots/orchard_spirit.jpg)

The full production target is **more than one million displayed prose words and 1,001 unique world sprites: 500 humans and 501 spirit beasts**, alongside the existing background quotas. Current delivery is **137,918 words and 23 original world sprites**. This expansion remains unfinished.

## Book V: The city of borrowed faces

Continue from any orchard settlement to a spring city where masks rent outward appearances and recognition credit for finite cultivation-furnace hours. A changed batch makes workers' permanent name proofs answer for commercial disputes. Compare substituted mask collars, trace the registry and courier bills, or test offered wax fragments with two controls. The other teams present their findings before public proofs are restored.

Choose a capped three-night credit bridge, separate permanent and temporary ledgers, a worker licensing cooperative, or an individual batch audit. The audit remains available without attribute training. All four outcomes keep genuine charges, fuel limits and unresolved work visible.

This chapter adds **119 scenes and 10,456 authored prose words**, four human originals and two spirit beasts at native **1024×1536 RGBA**, and a separate **1536×1024** market painting. Native pixels are retained in lossless WebP; these are independently painted designs.

![Qiao Sen in his mask workshop](docs/screenshots/city_mask_maker.jpg)

![The independent Porcelain Courser](docs/screenshots/city_courser.jpg)

![The Glasswing Moth](docs/screenshots/city_moth.jpg)

![City resolution choices](docs/screenshots/city_choices.jpg)


## Book VI: The court above the rain

Follow four investigations into an accident at a cliff court: arrange safe witness access, compare bounded rain and clock records, account for finite assistance, or trace conflicting docket versions. An injured porter and stonebinder need their corrected work proofs honored while particular safety and injury questions remain open. Paid carrying chairs use a covered footpath; the damaged goods lift stays closed.

The court admits approved records, corrects an unsupported broad assessment, and keeps genuine claims and ordinary care in place before the final choice. Fund one of four bounded next steps: weather observations, local testimony, staged source checking, or an ungated limited remand. Existing funds cannot buy every remedy at once.

Book VI adds **784 scenes and 75,090 displayed prose words**, four independent human portraits, the Rain Heron, and three native court environments. The campaign loads authored books from a manifest while preserving existing scene IDs and version-1 saves. All bundled narration uses compressed Vorbis, with text hashes and source encoding recorded in its manifest.

![He Lian and the initial petition](docs/screenshots/court_upper_bench.jpg)

![The Rain Heron](docs/screenshots/court_rain_heron.jpg)

![Four inquiry routes](docs/screenshots/court_investigation_choice.jpg)

![Bounded court remedies](docs/screenshots/court_final_choice.jpg)

## Book VII: The circle that kept a crossing

Return to the river three days after the court review. Follow the reed-channel maintenance record, volunteered archive extracts, or Wei Jin's damaged former ferry approach. Each team brings independent evidence to a common comparison. The third ring stays sealed while its living owner is identified through offered records.

Wei Jin separately accepts a closed return, three paid custody watches with review, or no return today under existing protection. The choice arranges tonight's work; it grants no listening permission. The original Book VII expansion added **257 scenes and 24,177 displayed words**. The later continuity review adds the mandatory ownership-context scene and recasts the marsh, archive and road power passages. Current campaign delivery is **137,918 words**; **862,083 displayed words remain** toward the strict million-word target.

Failed save replacement preserves a verified prior checkpoint; a missing primary can recover that backup. Scene transitions resume effects after dismissing a popup. Narration generation retains completed clips after a failed batch, and the Godot loader rejects duplicate JSON keys.

## Clothing options

Open **Wardrobe** in the top navigation and choose an outfit independently for each character.

| Outfit | Style |
|---|---|
| Sect Robes | Layered cultivation robes |
| Light Training | Sleeveless wraps and open martial vests, exposed arms and waists, split skirts |
| Moon Festival | Open shoulders and backs, decorated silk, open necklines and high side slits |

The four adult characters each have all three options. Gallery previews animate, selected clothing appears immediately in the story and on the title screen, and choices persist across sessions. Clothing changes preserve dialogue progress and cultivation stats.

![Light Training wardrobe](docs/screenshots/wardrobe_training.jpg)

![Moon Festival wardrobe](docs/screenshots/wardrobe_festival.jpg)

## Animation in motion

Each character and outfit uses one intact portrait. Godot gently moves the whole body up and down in a four-second loop. These previews use the same portraits and bob settings:

![Animated Sect Robes](docs/animations/sect.webp)

[Light Training](docs/animations/training.webp) · [Moon Festival](docs/animations/festival.webp) · [Four motion cycles](docs/animations/motions.webp) · [Frame comparison](docs/animations/sect_frames.jpg)

The following recording samples the running Godot viewport, with background motion disabled:

![In-game character animation](docs/animations/rendered_game.webp)

The twelve resting portraits come from the original GPT artwork. Body bobbing preserves each complete drawing. The four story motion labels select a gentle 6–10 pixel bob, and reduced motion leaves the portraits still.

## Generated art and audio

| Asset | Delivered |
|---|---|
| GPT Images artwork | 24 gesture key poses, twelve outfit reference portraits, one mountain-sect environment |
| New world paintings | 8 original backgrounds + 32 extra interiors, 14 human NPCs, 7 spirit beasts, 3 items, 1 qi effect |
| Character portraits | **12 intact portraits**: 4 characters × 3 outfits |
| Animation playback | Sprite2D whole-body bobbing on a four-second loop |
| Music | Original 48-second pentatonic plucked-string composition |
| Sound effects | Page, bell, qi channeling, and sword |
| AI voices | Piper neural narration for all 1,471 scenes; one Lessac narrator timbre with character pacing |

Portraits are extracted from GPT artwork and bobbed by Godot at runtime. The game has no lip sync. See [art provenance](assets/art/PROVENANCE.md) and the generated voice model card for sources and licensing.

## Rebuild assets

Python 3.12 and ffmpeg are required to regenerate narration.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python tools/build_assets.py
python tools/generate_voices.py
python tools/validate_assets.py
python tools/preview_animations.py
```

Voice generation downloads the public Piper Lessac neural model on its first run. It needs no API key, resumes unchanged lines, and records the model source, SHA-256, upstream model card, codec, and per-line audio hashes. New clips use 16000 Hz mono Vorbis quality 0; validated existing clips are reused.

World art and descriptions live in `data/world_assets.json`. `tools/validate_world.py` checks references, native dimensions, transparency, reachability, and honest manuscript accounting.

To add appearances or adjust bobbing, update `data/wardrobe.json` and the GPT pose sheets. The campaign index lives in `data/story.json`; new authored books live in `data/books/` and are merged through its `books` manifest. See [story authoring](docs/STORY_AUTHORING.md) for ID, word-accounting and narration rules. See [development instructions](docs/DEVELOPMENT.md).

## Architecture

```mermaid
flowchart TD
    GPT["GPT Images · resting portraits"] --> Prep["Python portrait extraction"]
    Prep --> Portraits["12 intact outfit portraits"]
    Portraits --> Cast["Sprite2D cast · whole-body bob"]
    JSON["Story manifest and books · 1,471 scenes"] --> State["Story state · choices · stats"]
    Canon["Continuity ledger · required evidence checkpoints"] --> Verify
    Effects["Scene effects · reduced motion"] --> UI
    State --> UI["Godot interface · journal · saves"]
    Wardrobe["Wardrobe catalog · saved outfit choices"] --> Cast
    Wardrobe --> UI
    Cast --> UI
    JSON --> Piper["Piper neural narration"]
    Synth["Original music and SFX synthesis"] --> Audio["Music / SFX / Voice buses"]
    Piper --> Audio
    Audio --> UI
    CI["GitHub Actions"] --> Verify["Gesture checks · routes · saves · UI"]
    Verify --> Capture["Screenshots · bob previews · timed game GIF"]
    Verify --> Build["Standalone Linux build and playback check"]
```

## Validation

CI checks intact portrait extraction, preserved proportions, source/code hashes, audio integrity, and narration coverage.

Godot exercises all 48 outfit/motion combinations, checking that the complete portrait bobs smoothly and rests when reduced motion is enabled. Tests also cover every story route and ending, atomic rejection of invalid choices, long-campaign saves above 100, damaged settings recovery, world art rendering, save corruption handling, wardrobe persistence, UI navigation, and settings. Xvfb captures screenshots and timed character playback. CI exports and launches a Linux package from a folder without the source checkout and checks clean shutdown.

The feature branch bundles verified assets and review media in separate commits. When media is unchanged, the bundle job preserves the current commit. PR checks do not push to branches.

## License

Project code and original story: [MIT](LICENSE). GPT artwork provenance is documented in `assets/art/PROVENANCE.md`. Piper's voice model card is bundled in `assets/generated/voices/MODEL_CARD` and the Linux package. Piper is a build-time dependency; the game plays rendered WAV and Vorbis audio.
