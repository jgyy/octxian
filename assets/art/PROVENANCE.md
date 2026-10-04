# Art provenance

## Current core character sources · 2026-10-03

The six former cast/pose sheets and twelve small derived portraits were removed and replaced with twelve independently generated native **1024×1536 RGBA** portraits. [CORE_PROVENANCE.md](CORE_PROVENANCE.md) identifies the four characters, all three outfits and retained source blobs. The builder copies the new masters byte for byte; Godot supplies whole-body bobbing and still reduced-motion playback. The original `azure_cloud.webp` mountain environment remains.

[THUNDERFEN_PROVENANCE.md](THUNDERFEN_PROVENANCE.md) records seven new Book IX originals. Historical world paintings and their creation evidence remain below. Counts attached to earlier batches describe those batches; the current catalog and `docs/content_report.json` give live delivery counts.

Music and sound effects are original deterministic synthesis. Narration uses Piper Lessac with one narrator timbre and character pacing; the source, model hash and upstream model card are bundled with generated voices.

## World native paintings

GPT Images generated these original assets during this expansion:

| File | Native size | Contents |
|---|---|---|
| `world/salt_lantern_valley.webp` | 1672×941 | Salt-lake village, terraces, bell tower, and lanterns |
| `world/su_lan.webp` | 1024×1536 | Adult bell keeper, intact full-body sprite with alpha |
| `world/wei_jin.webp` | 1024×1536 | Adult ferryman, intact full-body sprite with alpha |
| `world/an_ru.webp` | 1024×1536 | Adult archivist, intact full-body sprite with alpha |
| `world/reed_listener.webp` | 1024×1536 | Spirit beast carrying salt reeds and a bell, sprite with alpha |
| `world/valley_archive.webp` | 1672×941 | Original ledgers, copied records, and lamplit archive interior |
| `world/north_landing.webp` | 1672×941 | Spring rain at Wei Xiu's ferry jetty |
| `world/bell_tower_square.webp` | 1672×941 | Autumn public square facing grounded ridges |
| `world/sheltered_reach.webp` | 1672×941 | High-bank mooring, willows, and resting empty ferry |
| `world/wei_xiu.webp` | 1024×1536 | Adult ferry pilot and stone carver, sprite with alpha |
| `world/mooring_eel.webp` | 1024×1536 | River spirit with bronze rings, sprite with alpha |
| `world/bronze_clapper.webp` | 1024×1536 | Detached bronze clapper and red cord, item with alpha |
| `world/sealed_echo_case.webp` | 1536×1024 | Reed case, closed mooring ring, and folded receipt, item with alpha |

The files retain the image tool's native pixels in lossless WebP and have not been upscaled. Native alpha and dimensions are validated in CI. They are new drawings, not recolors or copies of the existing cast. The image tool was asked for its highest native resolution; these are the returned dimensions, not a claim that a larger raster size contains more original detail.

The requested final inventory is 100 original-scope backgrounds, 500 human NPC originals, 501 spirit-beast originals, plus 100 additional building-interior backgrounds. This draft delivers seven original-scope backgrounds, 32 extra interiors, thirteen human NPCs, six monsters, and two additional item paintings. See `data/world_assets.json` and `docs/EXPANSION.md` for exact counts and remaining scope.

The original Salt Lantern Valley view depicts the period before Azure Cloud's fate is decided. Shared later scenes use the bell-tower square, whose framing does not assume the mountain remains aloft. None of the new paintings is an atlas crop. Native sprites and items are displayed with uniform scaling.

## Additional building interiors

GPT Images generated each painting in `world/interiors/` independently during the continuation of PR #2. The image tool returned a complete native PNG for each location. None is an atlas crop, resized derivative, recolor, or duplicated file. The [interior inventory](../../docs/INTERIORS.md) lists names, exact returned dimensions, and Git blob identifiers. All native RGBA pixels are preserved in lossless WebP. `compression.json` records original PNG SHA-256 hashes, new file hashes, and decoded pixel hashes.

The collection currently contains **32** paintings against the additional **100**-painting quota. Some locations belong to planned later books; gallery availability is delivered art, not a claim of written chapters.

## Original sprite production · 2026-10-03

The expanded target is **500 human portraits and 501 spirit beasts: 1,001 independent original designs**. Outfit variants, poses, recolors, mirrors, repackaged files, and cropped atlases do not qualify as separate designs. Each new sprite is generated separately at the image tool's requested highest native portrait resolution. Returned dimensions are recorded without claiming that enlargement adds detail.

| ID / original file | Native size | Original Git blob | Creation and design review |
|---|---|---|---|
| `ren_qiao` · `world/ren_qiao.webp` | 1024×1536 RGBA | `d96b92e7c67e79662308f6c975106af3fccfefbd` | Independently generated adult orchard healer; angular face, plum robes, green medicinal apron, ceramic salve jar, carved staff, medicine satchel. Reviewed as a distinct human design. |
| `frostroot_hart` · `world/frostroot_hart.webp` | 1024×1536 RGBA | `e6b08e4bbb97d99d6ba5be179e960633768d296f` | Independently generated winter deer spirit; root mane, asymmetrical crystal antlers, plum buds, bronze token. Reviewed as a distinct creature design. |

These paintings preserve the image tool's native pixels in lossless WebP. The catalog points to each retained original and this creation record. CI checks alpha, dimensions, bytes, decoded painting fingerprints, and original source references. Such checks detect copying and repackaging; editorial inspection establishes distinct identities and species.

Current original sprite delivery: **13 humans + 6 spirit beasts = 19**. The remaining sprite requirement is **487 humans + 495 spirit beasts = 982**.

## Book V originals · 2026-10-03

Each following painting was generated independently with GPT Images. The sprite requests specified a single complete character on transparent alpha and the generator's highest native portrait resolution. The returned portraits are **1024×1536 RGBA**; the city painting is **1536×1024 RGB**. These dimensions describe actual native outputs. The native pixels are retained as lossless WebP at the catalog paths.

| ID / original file | Native size | Original Git blob | Independent design |
|---|---|---|---|
| `qiao_sen` · `world/qiao_sen.webp` | 1024×1536 RGBA | `50e52ac3756587dd4a2062930e1ad1447fb2e6c5` | Adult mask maker: broad face and build, silver crown braid, ochre tunic, indigo tool apron, carved red mask and chisel. |
| `mei_dulan` · `world/mei_dulan.webp` | 1024×1536 RGBA | `69993801c29dfae58cfea2b6ce7b50239a9d0a98` | Mature registrar: silver braided updo, spectacles, charcoal-violet robes, ivory sleeves, folded archive slips. |
| `tao_wen` · `world/tao_wen.webp` | 1024×1536 RGBA | `ce492510b751b2e37207109e951d6356336fd876` | Adult courier: compact runner silhouette, black hair and orange headband, teal split coat, orange dispatch satchel. |
| `fei_nuo` · `world/fei_nuo.webp` | 1024×1536 RGBA | `876f7d324920ce7e1037f70fc6fd45f7a77e2030` | Adult perfumer: dark skin and long low braid, brick-red jacket, aqua skirt, scent vial and porcelain dish. |
| `porcelain_courser` · `world/porcelain_courser.webp` | 1024×1536 RGBA | `080a65e7582744c4b091ab44c507c81e4df4c622` | Equine courier spirit: four articulated hooves, blue-and-white porcelain plates, shard mane, pale flowing tail and delivery ledger. |
| `glasswing_moth` · `world/glasswing_moth.webp` | 1024×1536 RGBA | `6b210d2ddedf41d66884d29e389f41ecfdb58157` | Insect spirit: six jointed legs, feathery antennae, segmented body and four expansive copper-veined translucent wings. |
| `borrowed_faces_market` · `world/borrowed_faces_market.webp` | 1536×1024 RGB | `6a6bc847ecb0b10ff354db4182bcaaab18174f55` | Independent spring market environment: mask and mirror stalls, rain gutters, blue/saffron awnings and registry steps. |

The four people and two beasts are separate new identities, not variants of the prior cast. They were inspected for complete silhouettes and distinct faces, costume, anatomy and painted detail. CI checks native dimensions, alpha, retained source references, file hashes and decoded painting fingerprints; rendered captures check their gameplay presentation. The market counts once toward the original background quota. The portraits add **4 humans + 2 spirit beasts**, bringing original sprite delivery to **14**; **987** remain.

## Book VI originals · 2026-10-03

GPT Images generated these eight paintings independently. Portrait requests specified transparent backgrounds and the highest native portrait resolution; environments requested the highest native landscape resolution. The original pixels remain unchanged in lossless WebP at their catalog paths. Each returned portrait is 1024×1536 RGBA and each environment is 1536×1024 RGB. No enlargement, crop, pose variant, recolor, or atlas cell counts as a new original.

| ID / original file | Native size | Original Git blob | Independent design |
|---|---|---|---|
| `he_lian` · `world/he_lian.webp` | 1024×1536 RGBA | `ee5ddb78a2bb7c187b7787785122d892f11c6dff` | Mature East Asian woman with the physical appearance of age 62, broad calm wrinkled face, deep brown eyes, white hair in three thick braids looped into a low crown, dignified strong upright build, deep burgundy judicial robe with dark blue outer panels and narrow pale brass trim, ivory inner sleeves, plain dark boots, one closed case folder held flat in both hands, small jade bench seal at belt; no weapons. |
| `luo_shan` · `world/luo_shan.webp` | 1024×1536 RGBA | `13c02a08a9598098a7d66ac0629c96f462795c14` | East Asian adult man age 39, thin long expressive face, medium tan skin, short dark hair tied in a very small topknot, slightly stooped slender build, moss-gray knee-length travel robe over ochre trousers, worn blue cloth shoes, patched slate writing apron, ink-stained fingertips, folded pale paper petition in left hand and slim brush case right hand, small woven document bag at hip. |
| `bai_qun` · `world/bai_qun.webp` | 1024×1536 RGBA | `0b09449b97ed9b175ccf53f34bdf27243cf332bd` | East Asian adult woman age 44, sturdy broad-shouldered working build, sun-darkened weathered face, a silver streak in black hair braided close down one side, muted forest-green short split work robe, thick brown leather stone apron, rolled sleeves over charcoal forearm wraps, gray trousers, robust pale leather boots, small square stonemason hammer in lowered right hand, measuring cord loop and repair chisel at belt, folded maintenance sheet in left hand, grounded practical stance. |
| `du_heng` · `world/du_heng.webp` | 1024×1536 RGBA | `8dbafa3dc1c169344dd8d93177e55bfdd229576a` | East Asian adult man age 31, lean tall working build, medium brown skin, narrow face with gentle tired eyes, shoulder-length black hair loosely tied with dark orange ribbon, rust-orange padded work coat over navy tunic, cream trousers and dark wrapped boots; his RIGHT shoulder and upper arm are bandaged beneath a modest simple cream support sling holding the right forearm across torso, his LEFT hand holds a small folded clean cloth, no blood, no visible wound, no dramatic pain pose. |
| `rain_heron` · `world/rain_heron.webp` | 1024×1536 RGBA | `53bf04f9a02572e832849dde5f34b286c02f8702` | A large elegant heron spirit with unmistakable natural bird anatomy, long S-curved pale silver neck, narrow long copper-gold beak, alert round dark eye, tall slate-blue feather crest, powerful rounded feathered white body with layered indigo gray wings folded asymmetrically, extremely long jointed dark blue legs with three-toed bird feet all visible, train of fine copper-tipped tail feathers, crystal dew beads on wing edges and one small brass rain gauge charm hanging at breast, no human face, no human limbs. |
| `rain_court_terrace` · `world/rain_court_terrace.webp` | 1536×1024 RGB | `2e987731c8d77dd65cf28ce6298c480152d3b38f` | An ancient Chinese fantasy court built securely into a huge fixed slate cliff above a valley of low spring rain clouds, broad wet pale-stone terrace with a shallow ramp and waist-high timber rails, burgundy-pillared court building under sober dark green tiles, anchored stone bridge at left, ordinary wooden goods sling and counterweight lift landing with visible ropes and brake wheel at right, modest plum branches, no floating mountain or suspended building, clear open foreground. |
| `rain_court_hearing_hall` · `world/interiors/rain_court_hearing_hall.webp` | 1536×1024 RGB | `a4525a704f5a30169fe46a1cb6e36da4dd2e375d` | Interior of an ancient Chinese cliff court hearing hall, grounded low stone magistrate bench at back with a simple pale brass seal stand, four movable wooden witness chairs at different heights, low tables with covered case folders, burgundy pillars and dark green rafters, broad clear central aisle with shallow ramps, high open windows showing soft spring rain clouds, practical rather than imperial, warm oil lamps, no throne or kneeling crowd. |
| `rain_court_witness_room` · `world/interiors/rain_court_witness_room.webp` | 1536×1024 RGB | `7f063c66ee677b7b2509daeb4c40f27e71f75708` | Quiet sheltered witness waiting room inside ancient Chinese cliff court, a long bench with folded cream blankets, separate small writing tables and blank papers, brass kettle on a safe low stove, hooks with empty spare rain capes, wide accessible doorway and level floor, blue-gray walls and timber beams, high rain-lit windows, one modest cot behind a half-open screen, clean practical rest space. |

Editorial review checked separate human identities, complete silhouettes, the porter's supported anatomical right arm, the heron's natural bird anatomy, and grounded accessible court spaces. These add **4 human originals + 1 spirit beast** for **19** delivered sprites. The terrace counts once toward the original background quota; the hearing hall and witness room count once each toward the additional interiors. Native dimensions, alpha, retained sources and distinct decoded paintings remain subject to CI validation.

## Storage compression

Artwork was losslessly re-encoded from PNG to WebP. Every RGBA pixel, including hidden RGB beneath transparency, and every native dimension was compared before removing the PNG. `compression.json` retains source PNG hashes and decoded pixel hashes. Original Git blob IDs above describe the pre-compaction files; those bytes are retained in the local recovery bundle rather than the rewritten remote history. Narration uses 16000 Hz mono Vorbis quality 0 and records its previous encoding and file hash for each clip.
