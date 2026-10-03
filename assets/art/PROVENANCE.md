# Art provenance

GPT Images created the following source images for Jade Vow on 2026-10-02:

| Source | Contents |
|---|---|
| `cast.webp` | Four adult characters in Sect Robes |
| `cast_training.webp` | Four Light Training outfit references |
| `cast_festival.webp` | Four Moon Festival outfit references |
| `poses_sect.webp` | Two distinct gesture poses for each character in Sect Robes |
| `poses_training.webp` | Two distinct gesture poses for each character in Light Training clothing |
| `poses_festival.webp` | Two distinct gesture poses for each character in Moon Festival clothing |
| `azure_cloud.webp` | Mountain-sect environment |

The cast is Lin Yue, Shen Qing, Elder Yun, and Mo Ran. All are adults. The outfit references and pose sheets use previous GPT artwork to maintain their identities. Light Training and Moon Festival show more shoulders, arms, chest, back, waist, or legs through sleeveless cuts, open martial vests, halter bodices, off-shoulder draping, and skirt slits.

There are twelve character/outfit appearances and **24 GPT-drawn poses**. Each pose sheet has four columns and two rows: a resting gesture and a raised cultivation gesture. The game uses the twelve intact resting portraits in the top rows.

The portrait builder crops each complete resting drawing and fits it into a transparent 384×512 image while preserving its proportions. Godot applies a gentle whole-body vertical bob to the intact portrait at runtime.

The idle, channeling, wind, and resolve labels select a gentle whole-body bob amplitude. The four-second loop runs in Godot and requires one portrait per appearance. The game does not perform lip sync.

The generated manifest records source, catalog, builder-code, and portrait SHA-256 hashes. Animated WebP files and contact sheets under `docs/animations` preview the body bob; `rendered_game.webp` samples the running Godot viewport.

Music and sound effects are original deterministic synthesis. Neural narration uses Piper's Lessac model; its source, hash, and upstream model card are bundled with generated voices. No person's voice is cloned. All characters share one narrator timbre with different pacing.

Artwork is stored as lossless WebP with exact native RGBA pixels checked against the original PNGs. `compression.json` records the source file and decoded pixel hashes. Narration uses 16000 Hz mono Vorbis quality 0; review media uses JPEG screenshots and lossless animated WebP.
