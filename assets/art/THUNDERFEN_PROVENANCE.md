# Thunderfen native art · 2026-10-03

These seven independent paintings were generated for Book IX with the image-generation tool. NPC and monster sources are original paintings with derivation `none`; their source and delivered path are identical. Backgrounds retain the tool's landscape output; portrait masters retain its full supported 1024×1536 canvas and the effect retains 1536×1024. No resizing, cropping, padding or enlargement contributes resolution or delivery credit.

The tortoise was generated again after a framing edit returned a smaller canvas; only the final 1024×1536 source below is delivered and counted. Core character wardrobe variants are recorded separately in [CORE_PROVENANCE.md](CORE_PROVENANCE.md) and do not count as additional unique NPCs.

| ID | Native pixels | Retained source / delivered path | Git blob identity |
|---|---|---|---|
| `thunderfen_ridge` | 1672×941 | `assets/art/world/thunderfen_ridge.png` | `27bcfb64485e164928f39b6b62d4e8e6e685f2b1` |
| `thunderfen_night` | 1672×941 | `assets/art/world/thunderfen_night.png` | `0fb7fdaa21524db5651d2deb0e363d4fab0418fe` |
| `jiang_tao` | 1024×1536 | `assets/art/world/jiang_tao.png` | `d7913b4bfb024ff38157340973254492644d4b2b` |
| `copperback_tortoise` | 1024×1536 | `assets/art/world/copperback_tortoise.png` | `eadc889dc259025f0dd61dc3d9284ad89c2e2b81` |
| `cloudhound` | 1024×1536 | `assets/art/world/cloudhound.png` | `49633efb143eecc83f2f3e9a887cf06a87e770dd` |
| `storm_compass` | 1024×1536 | `assets/art/world/storm_compass.png` | `923d281fc916e1372ffed8c6b653f174e29eee42` |
| `storm_discharge` | 1536×1024 | `assets/art/effects/storm_discharge.png` | `37522d85cad672e3bf8e5ff655946b34094763de` |

`tools/validate_world.py` checks native dimensions, alpha on foreground art, independent retained sources and decoded painting fingerprints. Byte hashes and pixel equality establish retention; the listed distinct designs remain reviewable in the originals and actual game screenshots.
