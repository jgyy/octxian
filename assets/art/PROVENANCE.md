# Art provenance

GPT Images created the following source images for Jade Vow on 2026-10-02:

| Source | Contents |
|---|---|
| `cast.png` | Four adult characters in Sect Robes |
| `cast_training.png` | Four Light Training outfit references |
| `cast_festival.png` | Four Moon Festival outfit references |
| `poses_sect.png` | Two distinct gesture poses for each character in Sect Robes |
| `poses_training.png` | Two distinct gesture poses for each character in Light Training clothing |
| `poses_festival.png` | Two distinct gesture poses for each character in Moon Festival clothing |
| `azure_cloud.png` | Mountain-sect environment |

The cast is Lin Yue, Shen Qing, Elder Yun, and Mo Ran. All are adults. The outfit references and pose sheets use previous GPT artwork to maintain their identities. Light Training and Moon Festival show more shoulders, arms, chest, back, waist, or legs through sleeveless cuts, open martial vests, halter bodices, off-shoulder draping, and skirt slits.

There are twelve character/outfit appearances and **24 GPT-drawn poses**. Each pose sheet has four columns and two rows: a resting gesture and a raised cultivation gesture. The game uses the twelve intact resting portraits in the top rows.

The portrait builder crops each complete resting drawing and fits it into a transparent 384×512 image while preserving its proportions. Godot applies a gentle whole-body vertical bob to the intact portrait at runtime.

The idle, channeling, wind, and resolve labels select a gentle whole-body bob amplitude. The four-second loop runs in Godot and requires one portrait per appearance. The game does not perform lip sync.

The generated manifest records source, catalog, builder-code, and portrait SHA-256 hashes. GIFs and contact sheets under `docs/animations` preview the body bob; `rendered_game.gif` samples the running Godot viewport.

Music and sound effects are original deterministic synthesis. Neural narration uses Piper's Lessac model; its source, hash, and upstream model card are bundled with generated voices. No person's voice is cloned. All characters share one narrator timbre with different pacing.

## World native paintings

GPT Images generated these original assets during this expansion:

| File | Native size | Contents |
|---|---|---|
| `world/salt_lantern_valley.png` | 1672×941 | Salt-lake village, terraces, bell tower, and lanterns |
| `world/su_lan.png` | 1024×1536 | Adult bell keeper, intact full-body sprite with alpha |
| `world/wei_jin.png` | 1024×1536 | Adult ferryman, intact full-body sprite with alpha |
| `world/an_ru.png` | 1024×1536 | Adult archivist, intact full-body sprite with alpha |
| `world/reed_listener.png` | 1024×1536 | Spirit beast carrying salt reeds and a bell, sprite with alpha |
| `world/valley_archive.png` | 1672×941 | Original ledgers, copied records, and lamplit archive interior |
| `world/north_landing.png` | 1672×941 | Spring rain at Wei Xiu's ferry jetty |
| `world/bell_tower_square.png` | 1672×941 | Autumn public square facing grounded ridges |
| `world/sheltered_reach.png` | 1672×941 | High-bank mooring, willows, and resting empty ferry |
| `world/wei_xiu.png` | 1024×1536 | Adult ferry pilot and stone carver, sprite with alpha |
| `world/mooring_eel.png` | 1024×1536 | River spirit with bronze rings, sprite with alpha |
| `world/bronze_clapper.png` | 1024×1536 | Detached bronze clapper and red cord, item with alpha |
| `world/sealed_echo_case.png` | 1536×1024 | Reed case, closed mooring ring, and folded receipt, item with alpha |

The files are the image tool's native PNG outputs and have not been upscaled. Native alpha and dimensions are validated in CI. They are new drawings, not recolors or copies of the existing cast. The image tool was asked for its highest native resolution; these are the returned dimensions, not a claim that a larger raster size contains more original detail.

The requested final inventory is 100 original-scope backgrounds, 500 human NPC originals, 501 spirit-beast originals, plus 100 additional building-interior backgrounds. This draft delivers six original-scope backgrounds, 30 extra interiors, nine human NPCs, five monsters, and two additional item paintings. See `data/world_assets.json` and `docs/EXPANSION.md` for exact counts and remaining scope.

The original Salt Lantern Valley view depicts the period before Azure Cloud's fate is decided. Shared later scenes use the bell-tower square, whose framing does not assume the mountain remains aloft. None of the new paintings is an atlas crop. Native sprites and items are displayed with uniform scaling.

## Additional building interiors

GPT Images generated each painting in `world/interiors/` independently during the continuation of PR #2. The image tool returned a complete native PNG for each location. None is an atlas crop, resized derivative, recolor, or duplicated file. The [interior inventory](../../docs/INTERIORS.md) lists names, exact returned dimensions, and Git blob identifiers. All original PNG bytes are preserved.

The collection currently contains **30** paintings against the additional **100**-painting quota. Some locations belong to planned later books; gallery availability is delivered art, not a claim of written chapters.

## Original sprite production · 2026-10-03

The expanded target is **500 human portraits and 501 spirit beasts: 1,001 independent original designs**. Outfit variants, poses, recolors, mirrors, repackaged files, and cropped atlases do not qualify as separate designs. Each new sprite is generated separately at the image tool's requested highest native portrait resolution. Returned dimensions are recorded without claiming that enlargement adds detail.

| ID / original file | Native size | Original Git blob | Creation and design review |
|---|---|---|---|
| `ren_qiao` · `world/ren_qiao.png` | 1024×1536 RGBA | `d96b92e7c67e79662308f6c975106af3fccfefbd` | Independently generated adult orchard healer; angular face, plum robes, green medicinal apron, ceramic salve jar, carved staff, medicine satchel. Reviewed as a distinct human design. |
| `frostroot_hart` · `world/frostroot_hart.png` | 1024×1536 RGBA | `e6b08e4bbb97d99d6ba5be179e960633768d296f` | Independently generated winter deer spirit; root mane, asymmetrical crystal antlers, plum buds, bronze token. Reviewed as a distinct creature design. |

These PNGs are the image tool's unmodified native outputs. The catalog points to each retained original and this creation record. CI checks alpha, dimensions, bytes, decoded painting fingerprints, and original source references. Such checks detect copying and repackaging; editorial inspection establishes distinct identities and species.

Current original sprite delivery: **9 humans + 5 spirit beasts = 14**. The remaining sprite requirement is **491 humans + 496 spirit beasts = 987**.

## Book V originals · 2026-10-03

Each following painting was generated independently with GPT Images. The sprite requests specified a single complete character on transparent alpha and the generator's highest native portrait resolution. The returned portraits are **1024×1536 RGBA**; the city painting is **1536×1024 RGB**. These dimensions describe actual native outputs. The unmodified PNG bytes are retained at the catalog paths.

| ID / original file | Native size | Original Git blob | Independent design |
|---|---|---|---|
| `qiao_sen` · `world/qiao_sen.png` | 1024×1536 RGBA | `50e52ac3756587dd4a2062930e1ad1447fb2e6c5` | Adult mask maker: broad face and build, silver crown braid, ochre tunic, indigo tool apron, carved red mask and chisel. |
| `mei_dulan` · `world/mei_dulan.png` | 1024×1536 RGBA | `69993801c29dfae58cfea2b6ce7b50239a9d0a98` | Mature registrar: silver braided updo, spectacles, charcoal-violet robes, ivory sleeves, folded archive slips. |
| `tao_wen` · `world/tao_wen.png` | 1024×1536 RGBA | `ce492510b751b2e37207109e951d6356336fd876` | Adult courier: compact runner silhouette, black hair and orange headband, teal split coat, orange dispatch satchel. |
| `fei_nuo` · `world/fei_nuo.png` | 1024×1536 RGBA | `876f7d324920ce7e1037f70fc6fd45f7a77e2030` | Adult perfumer: dark skin and long low braid, brick-red jacket, aqua skirt, scent vial and porcelain dish. |
| `porcelain_courser` · `world/porcelain_courser.png` | 1024×1536 RGBA | `080a65e7582744c4b091ab44c507c81e4df4c622` | Equine courier spirit: four articulated hooves, blue-and-white porcelain plates, shard mane, pale flowing tail and delivery ledger. |
| `glasswing_moth` · `world/glasswing_moth.png` | 1024×1536 RGBA | `6b210d2ddedf41d66884d29e389f41ecfdb58157` | Insect spirit: six jointed legs, feathery antennae, segmented body and four expansive copper-veined translucent wings. |
| `borrowed_faces_market` · `world/borrowed_faces_market.png` | 1536×1024 RGB | `6a6bc847ecb0b10ff354db4182bcaaab18174f55` | Independent spring market environment: mask and mirror stalls, rain gutters, blue/saffron awnings and registry steps. |

The four people and two beasts are separate new identities, not variants of the prior cast. They were inspected for complete silhouettes and distinct faces, costume, anatomy and painted detail. CI checks native dimensions, alpha, retained source references, file hashes and decoded painting fingerprints; rendered captures check their gameplay presentation. The market counts once toward the original background quota. The portraits add **4 humans + 2 spirit beasts**, bringing original sprite delivery to **14**; **987** remain.
