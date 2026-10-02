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

There are twelve character/outfit appearances and **24 GPT-drawn animation key poses**. Each pose sheet has four columns and two rows: a resting gesture and a raised cultivation gesture.

The frame baker extracts a stable body portrait and upper-arm, forearm, and palm cutouts. The alternate pose supplies the moving limb textures and a donor clothing plate beneath the resting arm. Arm segments articulate along a curved hand path; the palm rotates with the forearm. Head tilt and hair/cloth deformation add secondary motion. Premultiplied alpha preserves the cutout edges.

Each appearance has four 64-frame cycles: idle, channeling, wind, and resolve. Total: **3,072 computed frames** in 48 PNG atlases, played by Godot at 16 fps. These are derived frames, not 3,072 independent GPT image requests. The game does not perform lip sync.

The generated manifest records source, catalog, rig, baker-code, and atlas SHA-256 hashes. GIFs and frame comparison sheets under `docs/animations` show the actual output; `rendered_game.gif` samples the running Godot viewport.

Music and sound effects are original deterministic synthesis. Neural narration uses Piper's Lessac model; its source, hash, and upstream model card are bundled with generated voices. No person's voice is cloned. All characters share one narrator timbre with different pacing.
