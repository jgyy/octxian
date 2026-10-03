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

The requested final inventory is 100 original-scope backgrounds, 500 human NPC originals, 501 spirit-beast originals, plus 100 additional building-interior backgrounds. This draft delivers five original-scope backgrounds, 30 extra interiors, five human NPCs, three monsters, and two additional item paintings. See `data/world_assets.json` and `docs/EXPANSION.md` for exact counts and remaining scope.

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

Current original sprite delivery: **5 humans + 3 spirit beasts = 8**. The remaining sprite requirement is **495 humans + 498 spirit beasts = 993**.
