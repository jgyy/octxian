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

## Book II native paintings

GPT Images generated these original assets during this expansion:

| File | Native size | Contents |
|---|---|---|
| `world/salt_lantern_valley.png` | 1672×941 | Salt-lake village, terraces, bell tower, and lanterns |
| `world/su_lan.png` | 1024×1536 | Adult bell keeper, intact full-body sprite with alpha |
| `world/wei_jin.png` | 1024×1536 | Adult ferryman, intact full-body sprite with alpha |
| `world/reed_listener.png` | 1024×1536 | Spirit beast carrying salt reeds and a bell, sprite with alpha |

The files are the image tool's native PNG outputs and have not been upscaled. Native alpha and dimensions are validated in CI. They are new drawings, not recolors or copies of the existing cast. The image tool was asked for its highest native resolution; these are the returned dimensions, not a claim that a larger raster size contains more original detail.

The requested final inventory is 100 new assets in each category. This draft delivers one background, two human NPCs, and one monster. See `data/world_assets.json` and `docs/EXPANSION.md` for exact counts and remaining scope.
