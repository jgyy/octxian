# Cultivation rewrite production ledger

Lin Yue begins as a mortal kiln worker with zero retained qi. She earns Body Tempering and the first three Qi Gathering stages through paid work, failed measurements, injuries, recovery and repeatable examinations. The pendant grants no cultivation.

## Delivered manuscript

| Measure | Actual delivered |
|---|---:|
| Mortal-training expansion | 77 scenes / 5,182 words |
| Rewritten original Book I | 36 scenes / 2,397 words |
| Sluice apprenticeship | 131 scenes / 7,892 words |
| Recast valley openings and power scenes | 22 scenes / 1,509 words |
| Other branch, power and continuity repairs | 34 scenes / 2,825 words |
| New ash-bridge foundry arc | 252 scenes / 18,874 words |
| Total cultivation rewrite | **552 scenes / 38,679 words** |
| Whole playable campaign | **1,858 scenes / 156,792 words** |
| Inherited prose awaiting recast | 118,113 words |

The prior [plot-hole review](PLOT_HOLE_REVIEW.md) repairs 41 existing scenes and adds four prerequisite scenes, producing **401 net displayed words** and **3,035 newly credited rewrite words**. Updated passages already credited are counted once. Metadata, canon, labels, outlines, documentation and art descriptions contribute zero manuscript credit.

[The machine-readable ledger](CULTIVATION_PROGRESS.json) lists every credited scene. The world validator recomputes the total, rewrite and inherited counts and rejects stale, duplicated or unknown credit. The strict target remains **1,000,001 words**: 843,209 additional displayed words are needed, or **961,322 rewrite words** for the complete rewritten manuscript. The fourteen-volume 1,050,000-word architecture is a plan.

## Earned progression

The [foundry arc](FOUNDRY_EXPANSION.md) adds 18,874 new playable words and earns the second pair on Day Eighty through three independent recovered trials. Work and creature-response branches share findings before mandatory gates.

The mortal opening reaches Qi Gathering stage one through three recovered retained-trace tests. During the repaired-road delay after Book I, Lin Yue works at the brine sluice for nearly three months. Stage two requires three calibrated six-unit overnight retention trials. Stage three requires three twelve-unit first-pair trials, compatible purity, interruption control and normal next-day sensation.

The arc separates reserve, route throughput, sampling discharge, delivery loss and ordinary fatigue. A salt bridge falsifies the caliper's return readings, prompting independent assessment, eleven rest days and a revised inspection. Reed-Step powers a rated cuff-to-sole stitch through the first arm pair; it never assumes an unopened leg channel works.

Three work/recovery options rejoin before stage two. Three mantis-response options rejoin after source isolation and before the valley journey. Crews and separate fuel carry the large ward loads. Choice attributes remain proficiency, separate from authored realm labels.

[The canon](CULTIVATION_SYSTEM.md) defines all twelve gates and provides the local second/third-stage assessment table. Open **Attributes → Cultivation realms** in the game.

## Native generated art

Nineteen cultivation masters are retained. The foundry continuation adds nine: three environments, three human portraits, one creature, one item and one interrupted-pair effect. The previous sluice batch added the **1536×1024 brine sluice workshop**, **1024×1536 RGBA Duan Zhi**, **1024×1536 RGBA brine mantis**, **1024×1536 RGBA meridian caliper**, and **1536×1024 RGBA paired-channel effect**.

The existing five cover the lower terrace, Han Mei, furnace mite, practice wick and first trace. [Provenance](../assets/art/CULTIVATION_PROVENANCE.md) records native generation. The image tool exposes no resolution parameter; requested maximum detail is reported at actual returned dimensions. No enlargement is credited.

The larger artwork library remains unfinished: eleven original-scope environments, 33 additional building interiors, eighteen human NPCs, nine monsters, five items and three effects are currently delivered. Effects do not count as world sprites.

## Validation and remaining production

The merged-data audit passes unique prose, the 100-word scene limit, character/art/stage references, actual gated reachability and every continuity checkpoint. All 1,858 scenes and 28 endings are reachable across 172,945 capped states. The campaign guards 45 mandatory continuity checkpoints. Books III–VII retain stage three; Book VIII earns stage four after its required recovered trials.

CI runs Python accounting and advancement regressions, native art and alpha checks, complete narration, Godot route/save/UI checks, fifty-nine actual viewport captures and standalone Linux launch. The final run and media commit are linked in the draft PR.

The complete million-word cultivation recast and the large world-art quotas remain unfinished. The current authored progression reaches stage four; later inherited prose still awaits recast. The codex is detailed reference lore rather than a full dynamic cultivation economy.

```mermaid
flowchart TD
    Mortal["Mortal · zero retained qi"] --> Body["Skin → Sinew → Bone → Marrow"]
    Body --> Trace["Three first-trace tests"]
    Trace --> One["Qi Gathering 1 · Book I novice"]
    One --> Sluice["Paid sluice apprenticeship"]
    Sluice --> Retention["Three recovered six-unit trials"]
    Retention --> Two["Qi Gathering 2 · Retention"]
    Two --> Failure["Route failure · instrument fault · recovery"]
    Failure --> Pair["Three recovered twelve-unit paired trials"]
    Pair --> Three["Qi Gathering 3 · First pair"]
    Three --> Work["Bounded mantis and valley work"]
    Work --> Foundry["Paid foundry work; warm-material failure; recovery"]
    Foundry --> Trials4["Three independent recovered eighteen-unit trials"]
    Trials4 --> Four["Qi Gathering 4 · Second pair"]
    Four --> Remaining["Later recast and million-word expansion"]
```
