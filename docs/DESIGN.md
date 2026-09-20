# Agent-Sora Podcast — Design Document

Status: OPERATIONAL (per-paper pipeline live; nightly cron armed)
Last updated: 2026-08-30 (new-machine migration; G2P/phoneme notes)

## Purpose

A podcast for a senior staff software engineer at a frontier AI lab: each
episode is a ~10-minute technical deep-dive into ONE paper, read by Isabella
(kokoro-82M, open weights), published as audio + RSS via GitHub Pages.
Dispassionate, implementation-focused; editorial contract in
`docs/STYLE_GUIDE.md` (verbatim producer brief from the show owner).

## Source & selection scope (user-defined)

- Feed: `https://huggingface.co/papers` (HF daily papers); arXiv fallback +
  HF backfill per the coverage process above.
- Topic rules (`config.yaml`): RL-for-text/agentic work, agent self-
  improvement, AI music generation, AI finance/econometrics, LoRA/PEFT for
  text/reasoning/agentic only; exclude image/video papers.
- Standing rules: foundation-model technical reports covered only when the
  day's top paper; topological-changes papers (looping, weight tying,
  adaptive computation, linear/fast-weight/SSM attention, latent CoT) always
  covered (2026-09-02).

## Episode granularity & dating (2026-09-20, user rules)

- **One episode PER PAPER.** Days may carry any number of episodes (cap was
  removed 2026-09-20: "having more than 6 per day is fine"; episodes are
  NEVER deleted).
- **Episodes are dated by PUBLICATION date, not paper date.** Filename
  `episodes/YYYY-MM-DD-<arxiv_id>.md`, front matter `Day:`, and the RSS
  `pubDate` all use the date the episode is published. Podcast players group
  by date and skip reloads when the newest item isn't newer — an old-dated
  item looks like "nothing changed" even though the feed changed. Backfilled
  papers therefore take the current publication date (e.g. 09-18 papers
  published 09-20 get `Day: 2026-09-20`); the paper's own date is not used
  for `Day:`.
- **Coverage process (2026-09-20, user rules):**
  1. HF daily re-check is the primary source (`fetch_papers.py` +
     `select_papers.py`); a day is "eligible" when its filter-passing
     papers (see config flavors + topology standing rule) are covered.
  2. **arXiv fallback**: if the HF daily doesn't yield enough filter-passing
     papers, `scripts/arxiv_search.py` searches arXiv AI sections
     (cs.AI/LG/CL/CV + q-fin + eess) over the same day window, per-flavor
     paced queries, deduped against HF cache ids and already-published ids.
  3. **HF backfill**: if recent days lack filter-passing topics,
     `scripts/backfill.py` walks prior papers-days (up to `--max-days`) and
     emits picks files for uncovered, filter-passing papers, upvote-ordered.
  All three run in the nightly cron prompt (steps 1a/1b/1c).

## Voice / TTS

- kokoro-82M (`hexgrad/Kokoro-82M`, Apache-2.0, CPU-friendly), voice
  `bf_isabella` ("Isabella", British) — user decision replacing KittenTTS
  "Rosie" (2026-08-24).
- ~10 min audio ≈ 25 min wall on this box (RTF ≈ 2.5×); serial-only synthesis
  (two concurrent jobs OOM-kill in this sandbox).
- `scripts/synth_kokoro.py` strips YAML front matter before speaking;
  `scripts/synth_batch.py` walks transcripts serially in a subprocess per
  episode, skips fresh mp3s (mtime vs transcript mtime), and refuses any
  transcript that fails `lint_script.py` (no wasted CPU on soon-to-change text).

### G2P / phonemes (verified 2026-08-29 on new machine)

- misaki English G2P has three tiers: curated lexicon → **inline overrides** →
  espeak fallback. Inline override syntax in transcript text:
  `[Word](/ipa ˈphoːnɪmz/)` — misaki honors the IPA verbatim (rating 5, never
  re-derived). This is the lever for fixing mispronounced terms: an LLM can
  write the phonemes directly into the transcript instead of trusting G2P.
- espeak is NOT a system dependency: `misaki.espeak.EspeakFallback` goes
  through `phonemizer` + `espeakng_loader`, and `espeakng_loader` BUNDLES
  `libespeak-ng.so` inside the venv. Verified working on a host with no
  espeak-ng installed (see `debugging/phoneme_override_test.py`, RESULT: PASS).
  If the fallback ever failed, KPipeline would degrade to silently DROPPING
  out-of-dictionary words (unk='') — that is the real failure mode to watch.
- `lint_script.py` does not flag the override syntax (no `\`, no `$`, no sci-
  notation), so overrides can live in transcripts without lint changes.
- NOTE for writers: overrides are markdown-link-shaped, so
  `synth_kokoro.py`'s link-stripping regex (`\[...\]\(...\)` → inner text)
  would eat them. If we adopt overrides in transcripts, the synth loader must
  pass them through (strip only non-phoneme links, or pre-resolve overrides).

## Pipeline

```
config.yaml                 # voice, topics, RSS metadata
docs/STYLE_GUIDE.md         # canonical editorial + file-format contract
scripts/fetch_papers.py     # HF daily papers listing
scripts/select_papers.py    # topic rules -> feed/selected-YYYY-MM-DD.json
scripts/paper_meta.py       # authors+affiliations (PDF page-1 legend),
                            # downloads+keeps PDFs -> feed/meta/<id>.{json,pdf}
scripts/pick_top.py         # true-upvote ranking -> top-6 picks/day
scripts/lint_script.py      # style gate: front matter, word band [1300,1750],
                            # cold open (title/3 authors/lab incl. corporate,
                            # possessive-tolerant), no LaTeX/$math$/sci-notation,
                            # violence-word scan, banned-style words, "!" budget
episodes/YYYY-MM-DD-<arxiv_id>.md   # transcripts (front matter + prose)
episodes/<same-stem>.mp3            # audio (gitignored; ships via gh-pages)
scripts/synth_batch.py      # lint-gated serial TTS
scripts/build_rss.py        # site/index.html + feed.xml from front matter;
                            # durations via ffprobe; LIVE base_url everywhere
scripts/publish.sh          # gh-pages clone/replace/push (+ .nojekyll — REQUIRED:
                            # Liquid-like {{ }} in abstracts break Jekyll builds)
cron e0646a456062           # nightly 03:00 UTC, prompt names per-paper format;
                            # skill agent-sora-episode carries the how-to
```

Transcript authoring uses parallel writer subagents fed meta JSON + extracted
full paper text (`episodes/feed/text/<id>.txt`) + STYLE_GUIDE; every file must
pass `lint_script.py` before synthesis.

## Delivery constraint (hard acceptance criterion)

The user listens ONLY via GitHub Pages: episode mp3 URL(s) AND feed.xml must
return 200 at `https://agent-sora.github.io/agent-sora/`. Verified live during
backfill rollout.

## Backfill (7 days, 2026-08-13 → 08-21): 42 episodes

- 42 papers = top-6/day by true upvotes across the 7 days; all transcripts
  lint-clean; synthesis runs serially (~7 h total) with incremental publishing.
- Old 7 per-day shows archived under `episodes/legacy-per-day/`.

## Alternatives considered

- One long episode per day (original shape): rejected — user asked for
  per-paper episodes of equal length instead.
- KittenTTS Rosie: replaced by kokoro bf_isabella (user decision, same day).
- Cloud TTS: no new subscriptions (user constraint).
- Uncapped per-day episodes (13–19/day): initially capped at 6; cap removed
  2026-09-20 (user: "having more than 6 per day is fine").
- LLM API for script generation: none available keyless; writer subagents +
  mechanical linter gate achieve the same contract enforcement.
