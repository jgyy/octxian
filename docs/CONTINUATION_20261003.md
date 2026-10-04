# Storm ledger and salt-road continuation — 2026-10-03

The playable manuscript contains **2,335 scenes / 190,875 displayed words** across eleven books, with 37 endings. This batch adds **336 scenes / 24,617 original displayed words**, plus 229 net words from existing-content repairs: **24,846 net added words**.

Only displayed node text earns manuscript credit. The strict target remains 1,000,001; **809,126 displayed words remain**. Full-production artwork quotas also remain unfinished and the PR stays draft.

## New story

[Book X — The storm that signed twice](STORM_LEDGER_EXPANSION.md) has 159 scenes and 11,961 words. Its three ingresses preserve Book IX's distinct outcomes. The inquiry separates warning failure, structural damage and a documented 38-copper relief diversion. Ordinary escape, a rated trolley, bounded external protection and paid recovery precede three different next steps.

[Book XI — Water for the names that stayed](SALT_ROAD_EXPANSION.md) has 177 scenes and 12,656 words. The restored nineteen households retain their standing while a separate old water-turn copy is corrected. Channel inspection, accounts and household listening provide independent findings. A usable-water clearance and finite reserve calculation precede trial and final allocation decisions. Rotation, maintenance and outside purchase leave materially different costs and reserves.

Lin Yue remains at earned Qi Gathering **4: Second pair**. New apparatus work and testimony train their corresponding capacities; player scores supply no realm, resource or another person's permission.

## Existing-content repairs

The prior PR audit records 115 corrections: 102 choice-causality/progression issues and thirteen prose passages. This continuation adds **53 distinct root continuity or causality defects across 78 existing paragraphs**. Repeated occurrences of one defect are grouped under one root record. New-scene draft revisions, art, documentation and renamed labels receive no repair credit. The PR therefore contains **168 audited existing-content corrections at this first milestone**; those categories are more precise than claiming 168 separate literary mysteries.

| Audit | New root defects | Existing paragraphs | Word delta |
|---|---:|---:|---:|
| [Books I–V](CONTINUITY_REPAIRS_20261003_OPENING.md) | 20 | 25 | +122 |
| [Court](CONTINUITY_REPAIRS_20261003_COURT.md) | 14 | 28 | −71 |
| [Ring](CONTINUITY_REPAIRS_20261003_RING.md) | 4 | 5 | +4 |
| [Cultivation and Thunderfen](CONTINUITY_REPAIRS_20261003_CULTIVATION.md) | 15 | 20 | +174 |
| Total | 53 | 78 | +229 |

Examples include a branch-only litter, rubbing or family introduction appearing on another route; private records opened without the promised room or permission; a loaded rope controlled through an explicitly unloaded tail; a filled-cup test that never loaded the cup; claims exceeding sealed-source observations; and a Thunderfen departure before the six-week bench contract ended.

All 78 complete before paragraphs were independently matched against source commit `8dd58078b349f27b228be1107599572bf850efdc`; all after paragraphs match the delivered files. IDs, graph and choice metadata were preserved for the existing prose repairs. The historical source index contains the 1,999 original node IDs and their actual files, excluding new scenes from repair credit.

Run:

```sh
python tools/validate_continuation_audits.py --source-base 8dd58078b349f27b228be1107599572bf850efdc --source-node-index docs/CONTINUATION_SOURCE_INDEX_20261003.json
```

The validator checks current anchors, counted roots, duplicate passages, no-op claims, source membership and path ownership. It supplements the documented editorial/source review.

## Four native originals

[Creation record](../assets/art/STORM_SALT_PROVENANCE.md) identifies retained original PNG bytes and Git blobs.

| Original | Returned native size | Story appearance |
|---|---|---|
| Thunderfen Warning Observatory | 1774×887 | `storm_warning_001`–`storm_warning_008` |
| Salt Lantern Water Mill | 1672×941 | `salt_channels_001` and shared operating reports |
| Yuan Lian | 1024×1536 RGBA | `salt_findings_003` |
| Reedglass Salamander | 1024×1536 RGBA | `salt_recovery_005` |

Maximum native detail was requested. The tool exposes no resolution control; recorded sizes are the actual returned outputs. Portrait alpha was inspected directly, and no enlargement is credited. The catalog now contains fourteen original-scope backgrounds, 34 additional interiors, twenty human NPCs and twelve spirit beasts.

## Verification

In-memory preflight checked all 2,335 reachable scenes, 37 endings, eleven chapter registrations, unique normalized prose, maximum 100 words per scene, speakers/actors/art references, nonnegative effects, 167 fact anchors and 51 mandatory checkpoint groups. Twenty-seven new prerequisite scenes dominate their final decisions across all six entrances.

The new audit validator has nineteen fixture regressions. Five integration tests protect chapter transitions, meaningful evidence/recovery prerequisites, earned stage, ungated completion and actual use of all four originals. Independent editorial reviewers examined both new books and their chronology, resources, knowledge and custody.

CI generates and hash-validates narration, runs Python and Godot traversal/save/UI checks, captures **72 actual game views**, validates timed body motion, exports Linux and launches the package without the source checkout. Publication of source precedes these checks; runtime and synthesized-media success is established by the linked workflow and its bundled report, not by the in-memory preflight alone.

A [second review](CONTINUATION_SECOND_20261003.md) adds 29 further roots / 33 paragraphs / 101 net words, bringing this request to 82 new roots and the PR overall to 197 categorized audited corrections. The playable counts above reflect that later repair; the first-batch additions and table remain historical.
