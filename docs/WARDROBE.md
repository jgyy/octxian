# Wardrobe assets

`data/wardrobe.json` is the shared catalog for the frame baker, validation, and Godot's
wardrobe controls. Each outfit has an ID, display name, short description, and a GPT source atlas.

The original `sect` style retains filenames such as `lin_yue_idle.png`. Other styles use
`lin_yue_training_idle.png` and `lin_yue_festival_idle.png`. Every atlas contains 64 RGBA
192×512 frames in an 8×8 grid, played at 16 fps.

The manifest records source and catalog hashes and groups every character and motion beneath
its outfit ID. The builder reuses unchanged atlases and migrates the verified original robes.
Use `python tools/build_assets.py --force` to rebake everything.

`scripts/wardrobe.gd` validates choices and restores defaults for invalid saved values.
Selections are saved in the `wardrobe/choices` section of Godot's `user://settings.cfg`,
independently of story saves. Every character's wardrobe persists across journeys and sessions.

CI validates all 3,072 decoded frame hashes, exercises all 48 playback cycles, checks dropdown
selection and persistence, and captures both new outfit sets plus an outfit in a story scene.
