# Wardrobe assets

`data/wardrobe.json` is the shared catalog for asset baking, validation, and Godot's wardrobe controls. Every outfit has an ID, display name, description, outfit reference atlas, and two-pose GPT sheet. `data/animation_rigs.json` supplies hand, elbow, shoulder, face, and hip landmarks in source-image coordinates for each appearance.

The original `sect` style uses filenames such as `lin_yue_idle.png`. Other styles use `lin_yue_training_idle.png` and `lin_yue_festival_idle.png`. Every atlas is an 8×8 grid of **384×512** cells, played at **16 fps**. The PNG uses palette compression with transparency; validation and Godot decode it into RGBA.

## Gesture baking

`tools/animation_baker.py` separates the two drawn poses at their transparent row seam, removes disconnected neighboring fragments, and aligns their feet. `tools/pose_rig.py` refines the palm landmark to opaque skin and constructs the arm path.

A stable portrait supplies the body. A donor plate from the alternate pose fills the area beneath its resting arm. Upper-arm, forearm, and palm textures from the raised pose move along an outward gesture arc. Their transforms use premultiplied alpha; the palm is excluded from the arm textures to avoid a duplicate hand. Neck-anchored head tilt and hair/cloth deformation add secondary motion.

The manifest groups every character and motion under its outfit ID. It records catalog, source, pose-sheet, rig-data, baker-code, and output hashes. Cached atlases are reused only when all these inputs and the expected dimensions match. This invalidates the old subtle-sway atlases. Run `python tools/build_assets.py --force` to rebake all appearances.

## Playback and persistence

`scripts/animated_character.gd` derives the cell width from the loaded atlas and constructs all 64 AtlasTextures for the selected outfit and motion.

`scripts/wardrobe.gd` validates choices and restores defaults for invalid saved values. Selections are saved in `wardrobe/choices` in Godot's `user://settings.cfg`, independently of story saves. Each character's wardrobe persists across journeys and sessions.

## Motion validation

All 48 loops must pass these checks on their decoded frames:

- After translation alignment, at least 7% of opaque body pixels and 12% of upper-body pixels change substantially between frames 0 and 32.
- The opaque silhouette changes by at least 2%; low-alpha qi particles do not count as body movement.
- The palm travels at least 48 pixels, and its 5×5 center patch has at least 80% coverage at alpha 160 or greater in six intermediate frames.
- Every one of the 3,072 decoded frames has a globally unique pixel hash.

Regression tests reject static portraits, the previous tiny sway/deformation, whole-body pans, tint changes, particles alone, and missing intermediate palms. Godot tests inspect loaded pose textures for every loop, exercise dropdowns and persistence, and verify frame advancement and reduced motion.

`tools/preview_animations.py` writes actual atlas GIFs, sampled-frame contact sheets, and landmark guides. Timed Godot viewport captures verify character movement with background motion disabled. CI publishes these under `docs/animations` and captures all three wardrobes plus selected clothing in a story scene.
