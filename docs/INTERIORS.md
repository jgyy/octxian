# Building interiors

The continuation of PR #2 requests 100 additional building-interior backgrounds, separate from the original 100-background quota. **10 are delivered; 90 remain.** Each file is an independently generated GPT Images painting preserved at its native returned dimensions. No scene is assembled from atlas cells, upscaled, or duplicated to inflate the inventory.

Open **World → Interiors** in the game to browse these locations. Locations for future books are art previews; their descriptions do not count toward the manuscript and do not imply those books are playable.

| Painting | Native size | Original PNG | Git blob |
|---|---|---|---|
| Bell Keeper's Workshop | 1672×941 | [bell_keeper_workshop.png](../assets/art/world/interiors/bell_keeper_workshop.png) | `17552ba16062fe164430659d6d80a957e4d8bf4c` |
| Ferry Ticket House | 1672×941 | [ferry_ticket_house.png](../assets/art/world/interiors/ferry_ticket_house.png) | `de0e1a7c408f941d364f76f809825705c07dbc9f` |
| High-Bank Boathouse | 1672×941 | [high_bank_boathouse.png](../assets/art/world/interiors/high_bank_boathouse.png) | `49770df151dd43432f76ac50580c30554bbb33d8` |
| Stone Carvers' Hall | 1672×941 | [stone_carvers_hall.png](../assets/art/world/interiors/stone_carvers_hall.png) | `217ad4dcfb52fa8bfad381623c07a6fd5851d4ef` |
| Reed-Case Workroom | 1672×941 | [reed_case_workroom.png](../assets/art/world/interiors/reed_case_workroom.png) | `71d593580c04cf4a8f81c09bac5fe736486f7e22` |
| Archive Copy Room | 1672×941 | [archive_copy_room.png](../assets/art/world/interiors/archive_copy_room.png) | `2bea8bacf153132762917762d4e13652d913ad85` |
| Archive Consent Room | 1672×941 | [archive_consent_room.png](../assets/art/world/interiors/archive_consent_room.png) | `edc8ff7334034da6a326661725a32688809e252e` |
| Village Council Room | 1672×940 | [village_council_room.png](../assets/art/world/interiors/village_council_room.png) | `113b418307dca60ab86427d12dce56a3f376e57e` |
| Salt Merchant's Store | 1672×941 | [salt_merchant_store.png](../assets/art/world/interiors/salt_merchant_store.png) | `9c3c2ac4e81d820c2183193b55fdbfdb2409e5b1` |
| Winter Grain House | 1672×941 | [winter_grain_house.png](../assets/art/world/interiors/winter_grain_house.png) | `ffd669ef7e1d105f48144f49d8fab4fbec0da021` |

The validator decodes every original, checks its recorded size and unique SHA-256, and keeps the extra collection separate in `delivered_additional_art`. Use `python tools/validate_world.py --require-complete` to require all manuscript and art deliverables.
