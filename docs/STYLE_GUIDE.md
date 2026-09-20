# Agent-Sora Daily — Episode Style Guide (canonical)

Source: verbatim producer brief from the show owner (2026-08-24). Every
transcript generator (backfill subagents AND the nightly cron) must follow this
exactly. Post-generation checks enforce the mechanical parts.

---

Create a very detailed explanation for the paper for an AI researcher that
would like to implement and test the ideas in the paper. The podcast should be
focussed on factual details, technical hurdles, and benchmarks. It should have
a skeptical, matter of fact, and gruff - but strictly professional - tone. The
details should come primarily from the paper PDF with the other sources as
supporting information, summaries and reviews just in case they are helpful.

Avoid speculation and hype! The podcast must use professional language, and
strictly avoid the use of slang, swear words, or any discussion of or metaphors
referring to violence. Never use any words like or related to "violence" (such
as "violently") unless they are specifically used in the reference text.

Remember that this is a podcast and it's very hard to understand spoken LaTeX.
Mathematical expressions should be rendered as words (numbers represented as
digits are also ok, but not scientific notation).

## Additional house rules

- FILE FORMAT CONTRACT: every transcript .md starts with YAML front matter,
  then the spoken prose. Fields (values come from
  episodes/feed/meta/<arxiv_id>.json):
      ---
      Title: <paper title>
      Authors: <first author, second author, third author>
      Labs: <affiliation 1; affiliation 2; ...>
      Arxiv: <arxiv id like 2608.12036>
      Day: <YYYY-MM-DD of the PUBLISH date (the day this episode is released),
           NOT the HF papers-day or arXiv submission date>
      Upvotes: <integer upvotes from meta json>
      Link: <https://arxiv.org/abs/<arxiv id>>
      Voice: <kokoro voice id, stamped automatically by scripts/synth_batch.py>
      ---
  The RSS builder parses these fields; missing fields break publication.
- DATE = PUBLISH DATE (standing rule, user 2026-09-20): filename is
  <PUBLISH-DATE>-<arxiv>.md and Day: = the same date, where PUBLISH-DATE is
  the day the episode is actually published (today for a nightly batch,
  including backfills). Rationale: podcast players key off pubDate to detect
  new episodes; an episode dated to the paper's older arXiv/HF date is
  invisible to the player as "new". Never re-date an already-published
  episode to an older date.
- COVERAGE RULES (standing, user 2026-09-20), in priority order:
  1. Always check HuggingFace daily papers first (the normal fetch/select
     path). A paper that is interesting to the audience and passes the topic
     filters gets an episode even if it missed the HF snapshot — fetch it
     directly from arXiv (scripts/paper_meta.py --ids-file) when HF has no
     record.
  2. ARXIV FALLBACK: if the HF shortlist for the day would yield fewer than
     3 episodes, run scripts/arxiv_search.py (last ~5 days of arXiv AI
     listings, per-flavor queries, deduped against the episode archive and
     the HF caches) and cover the top 2-4 hits as extra episodes.
  3. HF BACKFILL: if recent HF days lack qualifying topics, run
     scripts/backfill.py to surface older cached HF days that still have
     uncovered filter-passing papers, and cover the most recent ones.
  Episodes are dated with the publish date per the rule above in every case.
  More than 6 episodes in a day is fine; never delete an episode.
- One episode = one paper. Target ~10 minutes of speech (~9,500 characters of
  prose; acceptable window 8,500–10,500, i.e. roughly 1,300–1,750 words).
- FOUNDATION-MODEL TECHNICAL REPORTS: if the day's papers include a technical
  report introducing a NEW foundation model (language, multimodal/embedding,
  embodied/VLA, world model, or similar base-model release), ALWAYS produce an
  episode for it — even when its true upvotes would not make the top-N cut.
  Qualifier check runs AFTER vetoes. A title containing "Technical Report" is
  not sufficient by itself: control/orchestration layers atop existing systems
  and method papers that merely fine-tune or use existing models do NOT
  qualify. Upvote ranking otherwise unchanged.
- REASONING-MODEL TOPOLOGY (standing rule, user 2026-09-02): ALWAYS include
  papers on topological/architectural changes to reasoning language models —
  looping / recurrent depth / weight-tied or shared-layer iteration, adaptive
  computation, alternative attention mechanisms (linear attention, fast-weight
  / state-space update rules), latent or continuous chain-of-thought — even
  when their true upvotes would not make the top-N cut, and even if that means
  more than 6 episodes in a day. Feedback "loops" (closed-loop agents,
  human-in-the-loop, control loops) do NOT qualify; the criterion is model
  architecture topology, not workflow loops. More than 6 per day is fine.
- Cold open (first paragraph, before anything else): the paper title, the first
  three authors, and the labs/universities/companies the authors are affiliated
  with (from the PDF's first page). Say affiliations as spoken names
  ("Stanford University", "MIT"), comma-separated.
- Audience: senior staff software engineer at a frontier AI lab who wants to
  implement and test the ideas. No hand-holding, no marketing voice.
- Structure suggestion: cold open → problem and prior-art gap → method in
  implementation-relevant detail (data, architecture, training/eval setup,
  hyperparameters when stated) → benchmark results with concrete numbers →
  ablations/limitations/negative results → skeptical assessment: what would I
  trust, what would I re-verify before adopting, engineering gotchas.
- Numbers: digits fine ("0.49", "12 percent"); NO scientific notation — write
  "about 1.2 million parameters", not "1.2e6".
- Speakable math: "attention score scaled by the square root of the head
  dimension", never "$\sqrt{d_k}$".
- End with a two-sentence bottom-line verdict. No calls to action, no "like and
  subscribe".
