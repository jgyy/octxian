# Million-word continuation · verified delivery

The playable campaign contains **1,124,725 prose words across 12,697 scenes and 17 books**. This connects 930,652 stored draft words and adds **3,198 new words in 46 closing scenes** to the previous 190,875-word campaign. Alternative playable branches count; menu labels, character biographies and documentation do not.

Source commit `140d597edb311bd3fe58a0de5d09cec8515fda59` passed both [PR CI](https://github.com/jgyy/octxian/actions/runs/37188210424) and [feature-branch CI](https://github.com/jgyy/octxian/actions/runs/37188206781). Those checks cover the authenticated 101-site repair audit, Python regressions, every reachable gated scene, saves, menu scrolling, keyboard access, completed-practice persistence, ensemble layout, layered motion, native artwork, every narration clip, 78 rendered captures and standalone Linux package playback.

Media commit `52847c88d2ab2d93139a0390f865a4222896e5df` bundles the tested narration, screenshots and animation previews. The six new capture files were visually inspected at their actual **1280×720** resolution:

| View | Review image |
|---|---|
| Three-person archive scene | [Archive ensemble](screenshots/archive_ensemble.jpg) |
| Five desert attribute roles | [Desert attributes](screenshots/desert_attributes.jpg) |
| Three-person forest scene | [Forest ensemble](screenshots/forest_ensemble.jpg) |
| New independent beast original | [Lanternwing Crane](screenshots/lanternwing_crane.jpg) |
| New independent environment original | [Archive courtyard](screenshots/archive_courtyard.jpg) |
| New independent human original | [Lan Fen](screenshots/archive_lantern_keeper.jpg) |

The three retained originals use their returned native PNG bytes: **1536×1024** for the courtyard and **1024×1536 RGBA** for both sprites. [Provenance](../assets/art/MILLION_WORD_PROVENANCE.md).

The [101-site source audit](CONTINUITY_REPAIRS_20261004.json) distinguishes 95 premature task rewards, three missing closing sequences and three absent continuations. It does not claim 101 unrelated engine defects or count new portraits and scenes as repair sites.

The manuscript target is met. Independent artwork quotas remain unfinished: 28 original environments, 41 extra interiors, 51 human NPCs and 13 beasts. The requested PR remains draft.
