# Character attributes

Lin Yue's attributes grow through choices and continue across all three books.

| Attribute | Meaning | Ways to grow |
|---|---|---|
| Qi | Spiritual energy for channeling wards and sharing their burden | Breathing practice and protective wards |
| Trust | Bonds that help people act together by choice | Listening, sharing responsibility, honoring permission |
| Insight | Understanding of vows, evidence, and possible solutions | Questions, inscriptions, comparisons |
| Resolve | The will to carry a promise through difficult decisions | Sword practice, protection, commitments |

Open **Attributes** in the header or press **C**. The four cards show current scores, ranks, descriptions, growth hints, and progress toward the next rank. Press **Esc** or Close to return to reading. The panel pauses reading and atmospheric effects.

| Points | Qi | Trust | Insight | Resolve |
|---|---|---|---|---|
| 0–2 | Dormant | Unproven | Searching | Untried |
| 3–5 | Kindled | Open | Observant | Rooted |
| 6–9 | Flowing | Reliable | Discerning | Tempered |
| 10+ | Resonant | Steadfast | Lucid | Unshaken |

Ranks describe growth. Choices use their exact point requirements. Scores keep increasing beyond the highest rank, up to the existing save-system integer limit.

Each choice shows its attribute changes. Gated choices show current/required points and remain disabled until every requirement is met. For example, sharing the mountain's seal requires **Qi 3**: Qi 2 displays **Locked: Qi 2/3**, while Qi 3 permits the choice and awards **Trust +1**. Requirements do not spend points. After a successful choice, the footer confirms its attribute changes and the displayed totals refresh.

Scores remain in version 1 saves. Ranks are derived when displayed, so existing saves need no migration, including scores above 100. New journeys start at zero.

Implementation: `scripts/attributes.gd` holds the catalog and rank thresholds; `StoryState.choice_details()` shares validation between previews and actual choices. Story and runtime tests cover rank boundaries, preview/application agreement, malformed requirements, atomic failure, save compatibility, panel pause behavior, choice layout, and updated UI totals. CI captures the attribute panel and gated choices and loads the panel in the standalone Linux package.

## Verified build

[PR CI](https://github.com/jgyy/octxian/actions/runs/37083215048) and [branch CI](https://github.com/jgyy/octxian/actions/runs/37083211470) passed on source commit `6be1aad5`.

- All 196 scenes and 10 endings remain reachable across 8,295 capped states.
- Attribute ranks, preview/application agreement, malformed requirements, legacy saves, modal pause behavior, refreshed totals, and every authored choice layout pass in Godot.
- Nineteen actual viewport captures include the attribute panel and visible choice requirements.
- Linux export and standalone playback pass, including loading the attribute panel without the source checkout.

The following media bundle changes only review captures and their recorded source hash.
