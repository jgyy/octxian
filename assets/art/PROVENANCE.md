# Art provenance

`cast.png` and `azure_cloud.png` were created with GPT Images for Jade Vow on 2026-10-02.

The cast source contains four separate portraits: Lin Yue, Shen Qing, Elder Yun, and Mo Ran.
The animation pipeline bakes 64 distinct frames for each of four motions per character:
idle breathing, qi channeling, wind sway, and resolve. Total: **1,024 animation frames**.

These frames are derived from GPT-generated artwork. They are not 1,024 separate GPT image
generation requests, distinct characters, or hand-drawn poses. Motion uses image deformation
and particles, rather than skeletal or facial animation. All four cycles are playable by
Godot's AnimatedSprite2D at 16 fps.

Music and sound effects are original deterministic synthesis. Neural narration uses Piper's
Lessac model; its source, hash, and upstream model card are bundled with generated voices.
No person's voice is cloned. All characters share one narrator timbre with different pacing.
