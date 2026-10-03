# Jade Vow expansion

## Delivered in this draft

- **196 playable scenes and 10,274 authored prose words** across three books.
- Book I: 36 scenes, 942 words, three endings.
- Book II: 73 scenes, 4,000 words, three investigations, nine approaches, four endings.
- Book III: 87 scenes, 5,332 words, four spring continuations, three river routes, six settlement approaches, three endings.
- Five original-scope painted backgrounds at native 1672×941.
- 30 additional building-interior paintings preserved at their individual native sizes; [inventory](INTERIORS.md).
- Four human NPCs and two spirit beasts at native 1024×1536 with alpha.
- Two inspectable item paintings: clapper at 1024×1536 and echo case at 1536×1024.
- Rain, reed light, soft bell ripples, and qi effects, paused by panels and stopped by reduced motion.
- Continuity ledger plus required-knowledge and safety checkpoints.
- Seventeen rendered viewport screenshots, complete narration coverage, and Linux package validation.

These are exact delivered counts. This draft does **not** fulfill the requested original 100 backgrounds, 100 human NPCs, 100 monsters, the extra 100 interior backgrounds, or a manuscript longer than one million words. An image-generation prompt is not a delivered asset. A plot outline, word budget, alternate playthrough, or repeated paragraph is not an authored word.

## Production target

The requested final manuscript must contain at least **1,000,001 displayed prose words**, counted once per authored scene. Choice captions, character biographies, README text, outlines, and the number of possible routes are excluded. The current counting convention is whitespace-delimited words, applied to the current scene text, including editorial revisions.

`python tools/validate_world.py` writes the actual inventory and manuscript size to `build/content_report.json`. Structural validation passes independently of the production target; a passing draft CI run does not mean the target is fulfilled. Run `python tools/validate_world.py --require-complete` to require all deliverables. The command writes the report and exits unsuccessfully while any quota remains unmet. The manually dispatched CI workflow exposes the same check through its `require_complete` input.

The continuation request adds **100 building-interior backgrounds** to the original 100 backgrounds: **200 backgrounds total**. Only paintings explicitly assigned to the `building_interiors` collection count toward the extra quota; those paintings do not also satisfy the original background quota. The existing valley archive remains part of the original five. Exact repeated scene prose is rejected instead of counted again.

Native image dimensions are recorded per asset. Keep the original generated file. Do not satisfy “highest possible resolution” by enlarging a smaller file, cropping many tiny atlas cells, or copying one drawing under multiple names.

## Campaign outline and budgets

The following twenty books have a combined **planned** budget of 1,020,000 words. These words have not been written. Budget alone does not satisfy the manuscript target.

| Book | Working title | Planned words | Central conflict |
|---|---|---:|---|
| I | The Star Beneath the Mountain | 51,000 | Consent and the captive star |
| II | The Valley That Kept Its Name | 51,000 | Shelter, records, and erasure |
| III | The River Without a Shore | 51,000 | A ferry carrying an exile's memories |
| IV | The Orchard of Unfinished Winters | 51,000 | Healing that transfers another person's pain |
| V | The City of Borrowed Faces | 51,000 | Identity sold as cultivation currency |
| VI | The Court Above the Rain | 51,000 | Immortal justice and mortal testimony |
| VII | The Thousand-Mile Funeral | 51,000 | Who may inherit a dead sect's vows |
| VIII | The Desert That Remembers Water | 51,000 | Restoring a river without erasing its new inhabitants |
| IX | The Library Beneath the Moon | 51,000 | A history that edits its readers |
| X | The Seven Unopened Gates | 51,000 | Guardians who can no longer refuse their duty |
| XI | The Sea of Returning Swords | 51,000 | Weapons seeking the lives they ended |
| XII | The Mountain of Small Gods | 51,000 | Worship, dependence, and chosen responsibility |
| XIII | The Winter Parliament | 51,000 | Beast clans and human villages sharing a refuge |
| XIV | The Hand That Unmade Heaven | 51,000 | The creator of the captive-star covenant |
| XV | The Republic of Wandering Souls | 51,000 | Dead citizens demanding a living vote |
| XVI | The Last Examination | 51,000 | Cultivation merit measured by sacrifice |
| XVII | The Storm That Asked Permission | 51,000 | A sentient calamity negotiating its arrival |
| XVIII | The Road Through Every Home | 51,000 | Companions' incompatible promises |
| XIX | The Sky We Could Not Carry | 51,000 | Limits to collective rescue |
| XX | A Vow Freely Left | 51,000 | Endings shaped by what each companion can refuse |

Each chapter must be individually written and edited, as requested. Each book also needs consequential branches, route continuity, character consistency, and reader-facing pacing before its word budget can be marked delivered. Future art must match the existing painted illustrations; scalable vector substitutes are outside the requested scope.

## Quest structure

```mermaid
flowchart TD
    Shared["The Shared Sky"] --> SharedArrival["Shared responsibility"]
    Covenant["A Vow Without Chains"] --> CovenantArrival["Freedom and debts"]
    Release["Where Mountains Take Root"] --> ReleaseArrival["Consequences of descent"]
    SharedArrival --> Hub["Salt Lantern Valley"]
    CovenantArrival --> Hub
    ReleaseArrival --> Hub
    Hub --> Ferry["Drowned boundary"]
    Hub --> Reeds["The accused Listener"]
    Hub --> Archive["Altered household records"]
    Ferry --> FerryChoices["Raise / share / ask for a vote"]
    Reeds --> ReedChoices["Escort / rewrite / bring families"]
    Archive --> ArchiveChoices["Publish / compare / seek consent"]
    FerryChoices --> Conclave["The bell-tower assembly"]
    ReedChoices --> Conclave
    ArchiveChoices --> Conclave
    Conclave --> Crossing["Open Crossing · trust 3"]
    Conclave --> Bell["Unstruck Bell · insight 3"]
    Conclave --> Seed["Seed of Winter · qi 3"]
    Conclave --> Ledger["Common Ledger · always available"]
    Crossing --> Spring["Outcome-specific spring continuation"]
    Bell --> Spring
    Seed --> Spring
    Ledger --> Spring
    Spring --> River["Wei Xiu and the entrusted echoes"]
    River --> Return["New return place · receive now / supported delay"]
    River --> Stair["Flood-safe ramp · paid stages / capped advance"]
    River --> Harbor["Sheltered harbor · eight days / regular berth"]
    Return --> Ring["Unidentified ring remains sealed"]
    Stair --> Ring
    Harbor --> Ring
```

## Content and review pipeline

```mermaid
flowchart LR
    Paint["Native GPT paintings"] --> Catalog["World asset catalog"]
    Catalog --> Validator["Dimensions / alpha / distinct files"]
    Script["Authored story JSON"] --> Routes["Godot route and save tests"]
    Script --> Count["Count displayed prose once"]
    Script --> Voice["Piper narration"]
    Catalog --> UI["World gallery and scene art"]
    UI --> Capture["Xvfb game screenshots"]
    Routes --> CI["CI validation"]
    Validator --> CI
    Count --> Report["Actual counts and unmet targets"]
    CI --> Package["Standalone Linux game"]
    Capture --> Review["PR screenshots and diagrams"]
    Report --> Review
```

## Bug fixes

- Validate a choice destination and every effect before changing stats or history.
- Use the same explicit integer ceiling for gameplay and save loading; saves above 100 are valid.
- Validate settings types and finite numeric values before applying sliders and toggles.
- Preserve journal prose literally rather than interpreting loaded text as BBCode.
- Allow the dialogue panel to scroll when longer prose wraps beyond its visible height.
- Give new speakers a default narration pace instead of failing on missing speaker timing.
- Position role labels after the measured speaker-name width so long names remain readable.
- Keep scene portraits below the navigation bar and above the footer throughout their bob; resizing a cached portrait updates its scale immediately.
- Copy the animation formats actually produced by the renderer; the old animation JSON glob broke screenshot bundling.
- Refresh bundled review media when deterministic story, art, or runtime input hashes change, even when generated voice files are unchanged.

## Continuity review

`data/continuity.json` records reviewed facts, chronology, custody, permissions, and intentional unresolved questions. It is updated with every delivered book. The validator checks that each required evidence or safety scene lies on every structural path to its named decision. Godot separately traverses the choices under stat gates.

Book II takes place in autumn; Book III begins the following spring on every settlement route. Only the release ending grounds Azure Cloud. Common valley art faces grounded ridges. Lin Yue retains the pendant. Wei Xiu is alive, and Su Lan's husband remains dead; erased household records do not erase or resurrect people.

River echoes are volunteered external copies, not missing pieces of minds. Three rings hold separate permissions. The unidentified owner is a deliberate unresolved question in all Book III endings; no route opens that echo to guess an identity. Each settlement makes continued care explicit.

These structural checks supplement an editorial reading of every new scene. They do not certify that every possible literary inconsistency has been eliminated.

The manuscript still needs **989,727** additional authored prose words to reach 1,000,001. The original art quotas still need **95 backgrounds, 96 human NPCs, and 98 monsters**. The two item paintings are additional assets and do not count toward those quotas. The extra interior quota has 30 delivered paintings and 70 remaining. These future-campaign locations are available in the gallery; their existence does not claim that the outlined books have been written.
