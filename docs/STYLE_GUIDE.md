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

- One episode = one paper. Target ~10 minutes of speech (~9,500 characters of
  prose; acceptable window 8,500–10,500).
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
