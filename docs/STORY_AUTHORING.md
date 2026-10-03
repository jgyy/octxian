# Adding authored books

The campaign starts in data/story.json. Its existing metadata and Books I–V stay in that file; an optional books array lists additional repository files in loading order:

    "books": ["data/books/book_vi.json", "data/books/book_vii.json"]

Every listed file must exist under data/books and contain exactly three dictionaries: chapters, characters and nodes. Define new IDs once. An existing chapter, character or scene must not be repeated in another file, even if its definition is identical. Characters already registered in the opening file remain available to every subsequent book, so a book that introduces no speakers uses an empty characters dictionary.

The Godot and Python loaders merge the complete manifest before following links. Scenes may therefore refer to destinations in another book. To connect a new book, give each preceding ending its appropriate continuation. Keep those earlier ending IDs and prose intact unless making a deliberate editorial correction. Save version 1 continues to store the selected scene, attributes and journal; the source-file boundary does not change the player's saved state.

Both loaders fail when a listed book is missing, malformed, outside the allowed directory or contains conflicting IDs. CI additionally rejects duplicate keys inside JSON objects. Loading never returns a partially merged campaign. StoryState can also accept a previously merged dictionary for traversal tests; this injection bypasses manifest reads.

Each node still needs its registered speaker, actor and displayed text, and exactly one of next, choices or ending. Keep displayed prose at 100 words or fewer per scene. Choice destinations and ending continuations must exist in the merged campaign. Register new chapters and review their chronology and evidence in data/continuity.json. All scenes must be reachable, and every gated decision needs an available path for players who have not earned its attributes.

For long campaigns, nonnegative attribute gains let route tests cap scores at the highest authored requirement without losing future availability. Raise requirements only when the narrative warrants them; routine later decisions can use the established thresholds rather than increasing the number of states the tests must explore.

Only node text counts toward the manuscript target. Titles, choice labels, character descriptions, plans, budgets, documentation and audio metadata do not count. The world validator rejects identical normalized scene paragraphs. Editorial review must also ensure that new prose develops scenes, decisions, people and consequences rather than repeating passages with cosmetic substitutions.

## Narration and packaging

Every displayed scene receives Piper Lessac narration. The generator checks its text hash, audio hash, actual decoded samples, channels, format and duration before reusing an existing clip. Valid legacy 16-bit mono WAVs retain their original bytes.

New or edited scenes are synthesized into temporary PCM and encoded as mono Ogg Vorbis at quality 3 using ffmpeg. The generator validates the compressed result before replacing a clip, then removes its temporary PCM and any obsolete alternative. Each manifest entry records the actual format, codec, sample rate, duration, text hash, audio hash and encoding provenance. The audio director loads Ogg first and retains WAV playback for earlier scenes.

The compressed format keeps each new batch practical without silently omitting narration. Soundfile checks the decoded audio directly, avoiding a separate probe process for every scene. Godot imports both formats, and runtime tests exercise available WAV and Vorbis playback.

The export preset includes book JSON explicitly. Packaged-game validation loads the complete campaign manifest from the exported game, so missing book files fail the build even when the title screen still starts at arrival.

Run the existing Python tests and world validator after an editorial batch. Full CI also generates and validates every clip, traverses all gated routes, tests saves and the UI, and checks the standalone package. Draft validation reports honest remaining quotas. The strict production check continues to require every requested word and artwork quota before the PR is complete.
