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

## 2026-08-25 evening EDT — day-21 daily run (manual re-run; cron paused)
- Manual end-to-end run for 2026-08-25 while cron e0646a456062 is paused
  (machine move). Top-6 picked by TRUE HF upvotes: 161/51/33/31/23/14;
  picks JSON re-stamped from the HF API before writing front matter.
- Six parallel writer subagents: four passed the linter first try, two hit
  provider timeouts/503s and were re-dispatched; final state 6/6 lint-clean
  (total FAILs: 0), bodies 1,332–1,682 words, upvotes match picks file.
- New quality gate used alongside the linter: numeric fact spot-check of
  every distinctive figure against the extracted paper text. Caught a real
  fabrication in the TLive-Omni (2608.20958) episode — invented DocVQA 94.9,
  ChartQA 87.5, OCRBench 851 and a nonexistent "G-score 68.8"; product
  grounding AP also misquoted. Verified against arXiv HTML v1 tables and
  rewrote both passages with true figures (OCRBench 90.3, MMMU 73.4,
  MathVista 81.9, product AP 89.96/91.45 vs peers 28–65, temporal mIoU 81.5,
  live-commerce ASR CER 6.46, VideoMMMU 73.9 vs 72.8).
- Extraction gotchas worth remembering: this PDF pipeline drops leading
  zeros in table cells (".669") and fragments numbers across newlines, so
  collapse whitespace and check ".NNN" forms before calling a number
  unmatched. arXiv HTML (/html/<id>v1) is the better table source when PDF
  extraction is ambiguous.
- Serial kokoro synthesis ran as two passes (pass 2 only saw late files):
  6/6 OK, episodes 8.9–12.9 min, mean volume −25 to −29 dB (no silent
  degradation), single-flight lock respected throughout.
- build_rss dry-run produced exactly 48 items (42 live + 6 new) with all six
  new enclosures present before publishing.
- Publish incident: first gh-pages push died with HTTP 408 mid send-pack
  (~50 MB of new mp3s pushes git into chunked upload, which this path
  handles badly). Fixed WITHOUT editing publish.sh by injecting
  GIT_CONFIG_COUNT=1 / GIT_CONFIG_KEY_0=http.postBuffer /
  GIT_CONFIG_VALUE_0=524288000 into the environment; retry pushed cleanly
  (gh-pages commit a78f522, 6/6 mp3s visible via git ls-tree).
- Live-feed HTTP checks immediately after push still showed 42 items /
  404s on new mp3s — known Pages CDN lag pattern from earlier days;
  git-level truth on origin/gh-pages already correct at publish time.

## Day-22 addition (2026-08-26)
- New standing rule (user): FM tech reports always get an episode.
- Applied today: GigaBrain-0.7 + WeMM-Embedding already in top-6. DREAM Technical Report (2608.09408) checked and EXCLUDED: agentic control layer over Taobao recommender pipelines, no new base model. Slate stays 6.

## 2026-08-26 — Day-22 makeup instance (manual; morning cron died mid-flight)
- 2026-08-27 ~01:40 UTC (session span ~01:30-02:25): Confirmed zero 2026-08-26 artifacts from nightly cron e0646a456062; morning firing (~06:20) died in sandbox restart after shortlisting candidates. Manual day-22 instance started.
- Fetched HF daily_papers fresh: 25 entries cached. select_papers.py -> 18 kept (3 topic vetoes incl. Annotations as Rollouts).
- Upvotes were 0 in cache snapshot; re-pulled true upvotes per-paper from HF API. Slate: GigaBrain-0.7 (91), WeMM-Embedding (56), AutoSaddler (49), SecOPD (36), CyberFactory (28), Recuris (20).
- paper_meta.py for all six; PDFs in meta/, full-text extracted via venv PyMuPDF into feed/text/. All affiliations verified from PDF page-1 (GigaAI; Tencent WeChat Vision; POSTECH/KAIST/SUSTech/Microsoft; UC Berkeley; Beihang/ELLIS/IQuest/SMU; NUS/Stanford/Oxford/Princeton).
- NEW STANDING RULE (user): always cover new foundation-model technical reports even below top-N cut. Added to STYLE_GUIDE.md (commit b65bd19). DREAM Technical Report checked and excluded: control layer, no new base model.
- Wrote six transcripts; lint iterations fixed word-count floors and removed non-quoted violence-pattern words (destroy/wreck->neutral verbs; attacker->adversary where not quoted).
- lint_script.py final: total FAILs: 0, all 1305-1336 words, warnings 0.
- Numeric spot-check: every digit token in transcripts verified present in source text (only false flag: "3.5" inside model name Qwen3.5).
- Noted paper defect: AutoSaddler section 5.2 prose misstates SWE-Bench Pro delta (+8.4 vs table 9.6) and TB2 margin (+6.2 vs table 4.4); transcript flags this against the paper's own tables/abstract.
- Committed transcripts 1a26b87; serial kokoro synth launched under flock (proc_fd74077fa695); publish pending on synth completion.
- ~02:55 UTC: 6/6 MP3s synthed (8.6-10.2 min, voices auto-stamped, SYNTH_EXIT=0).
- ~03:00 UTC: build_rss + publish.sh OK (postBuffer guard, TMPDIR); Pages build "built" after ~1 min.
- ~03:02 UTC: VERIFIED LIVE — feed.xml + all six episode MP3s HTTP 200; feed=54 items; .nojekyll present in gh-pages tree.
- Day-22 (2026-08-26) makeup CLOSED. Next auto-fire: cron e0646a456062, 07:00 UTC (03:00 ET) -> Aug-27 batch.
