# Work Log — Agent-Sora Podcast

All timestamps UTC.

## 2026-08-24

- Wrote `scripts/audition_voices.py` to enumerate KittenTTS voices, synth a fixed
  sample as each, and benchmark CPU RTF.
- BUG found & fixed: `generate()` returns a single waveform ndarray (NOT
  `(audio, sr)`); sample rate is fixed 24000 Hz. Script updated (line 44).
- Ran audition (8 voices, biggest model `kitten-tts-mini-0.8`, CPU) with
  `TMPDIR=/workspace/.tmp` (espeak-ng needs exec-able dir). Clips + manifest in
  `audition/`.
- **Voice DECISION (user, by ear): ROSIE.** RTF 1.15 (~35 min to synth a 30-min
  episode). Recorded in `config.yaml` (`TTS_VOICE: "Rosie"`).
- Created `config.yaml`, `docs/DESIGN.md`, this log; initialized git repo
  (commit 29f717e).
- User constraint: podcast is consumable ONLY once live on GitHub Pages (mp3 +
  RSS both resolvable). Recorded as hard acceptance criterion in DESIGN.md.
- NEXT: `gh-setup` (create agent-sora repo, enable Pages, verify token scopes).
## 2026-08-24 13:40 UTC — first publish + e2e fixes
- build_rss.py: fixed missing `import sys`; cover.png now prefers real artwork from assets/cover.png.
- Generated proper 1400x1400 cover art (Pillow installed into .venv via uv).
- publish.sh: now also copies episodes/*.mp3 into the deploy tree (audio previously would have 404'd).
- Built site from ep1 (2026-08-21.mp3, 14.9 MB), pushed gh-pages commit 8041b38; raw.githubusercontent confirms all files present; awaiting Pages CDN rebuild for github.io URLs.

## 2026-08-24 ~13:50 EDT — Per-paper pivot (user decision)
- User replaced Rosie/KittenTTS with kokoro-82M `bf_isabella`; format now ONE
  ~10-min episode PER PAPER (top-6/day by true HF upvotes), not one daily show.
- Captured user's editorial brief verbatim in docs/STYLE_GUIDE.md (skeptical,
  gruff-professional, no hype/slang/violence metaphors, math as words, no
  scientific notation, PDF-first sourcing).
- paper_meta.py fixes: persist PDFs permanently; affiliation legend scanned on
  full page 1; case-sensitive keyword regex; citation-line junk filtered;
  manual patch for 2 layout outliers (2608.05604, 2608.13606).
- Upvotes were scraped as 0 -> now pulled from HF API for all 112 candidates;
  re-picked top-6/day (18 slots changed).
- build_rss.py rewritten for per-paper episodes (front-matter parsing,
  itunes:duration via ffprobe, newest-day-first ordering verified by smoke test).
- synth_batch.py added: serial subprocess-per-file synthesis (OOM-safe),
  resumable, skips existing >10KB mp3s. bf_isabella smoke-tested OK (~15s wall
  per minute of audio -> ~11h for 42 episodes, runs overnight).
- Legacy 7 daily episodes+mp3s moved to episodes/legacy-per-day/ (out of publish path).
- agent-sora-episode skill rewritten for the new pipeline; nightly cron e0646a456062
  inherits it (prompt defers to skill).
- Validated live publish path early with 2 episodes: build_rss -> publish.sh
  (gh-pages clone/replace/push), feed.xml 200, episode mp3 200 live.
  Episode runtime spot check: 589s (~10 min) per-paper target hit.
- All 42 transcripts lint-clean. Two writer agents had to be respawned for
  missed papers (day 14 x4, day 18 x1) plus a day-20 length-repair pass;
  steering + lint-gate caught every violation before TTS.
- Linter false-positive class fixed: lab-name matching now tolerates
  possessive/case variants ("Tencent's Hy Frontier team").
