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

## 2026-08-27 (day-23 manual makeup — Aug-27 cron died at startup)

2026-08-27 11:20 UTC CRON ANSWER: scheduler shows job e0646a456062 fired 03:08 ET, status=error; no session transcript exists (unlike Aug-25/26 runs); disk confirms zero artifacts — no papers-2026-08-27 cache, no selected-2026-08-27.json, no episodes. Third failure mode in three days. Started manual makeup.
2026-08-27 11:40 UTC SELECTOR AUDIT: select_papers.py had TWO silent gaps — (1) include-flavor fragments too narrow, so VoiceMem (101 up, #1 of day!) never matched any lane and was dropped WITHOUT a log line; (2) 'dropped' status never printed → 4 invisible drops. Fixed: broader agent/memory/conversation/coding fragments; word-boundary \bface\b veto (was 'face ' substring, killed papers containing 'interface'); DROP lines now always printed. Re-run kept=18 vetoed=7 dropped=3, total=28 accounted.
- Merit rulings: VoiceMem IN (#1); Handoff Tax / Code World Model / Rubrics-as-Visual-Repair out on rank (<cut); Video-IFBench & Real-TurnTurk out-of-lane. FM-tech-report sweep over all 28 abstracts: none introduce a new foundation model → rule adds nothing today.
- SLATE (true upvotes): VoiceMem 2608.26005 (101), FrontierChallenge 2608.24979 (99), WarpSAC 2608.24479 (85), JIT-Agent 2608.25593 (42), D3-MOPD 2608.24987 (18), Agent-G2 2608.23318 (17).
2026-08-27 12:05 UTC META/PDFs: paper_meta.py --cache-dir episodes/feed/meta OK 6/6; page-1 text extracts to episodes/feed/text/*.txt (pymupdf; grep needs -a flag, files contain control chars).
2026-08-27 13:30 UTC MINING: full read-through x6 → verified-facts blocks /workspace/.tmp/day23_facts*.md. Notable catches: FrontierChallenge has NO individual authors ('Apodex Team' byline; cold-open handled without fabricating names) and true subtitle 'Evaluating Scientific Workflow Completion', 12 models not 11; WarpSAC affil line-2 leaked body text in meta JSON (use line 1); JIT AgentIF-Oneday naming confirmed; VoiceMem Ze An is NUS not Tsinghua (superscript mapping checked before finalizing cold open).
2026-08-27 14:10 UTC DRAFTING: 6 transcripts written direct-to-lint-loop; iterative word-count top-ups (1300 floor) and accuracy fixes. lint_script catches that mattered: violence-word 'Killing'->'Removing' (D3-MOPD); cold-open parser counts Title-cased pairs incl paper title words (AllSpark/Apodex team-only papers pass via title case - documented behavior).
2026-08-27 14:40 UTC SPOT-CHECK sweep: 37 regex patterns vs transcripts -> 4 gaps closed: VM 134ms/430tok explicit, 49.8% emergent share explicit, EverMemOS/MemOS values inserted, WS '211 dimensions'. Fuzzy-patch caution logged: two patch anchor misses corrupted adjacent text mid-edit (caught+fixed same turn by reading back diffs).
- LINT FINAL: all six total FAILs: 0; words: G2 1309, WarpSAC 1323, FC 1308, D3 1362, JIT 1381, VoiceMem 1519.
2026-08-27 14:45 UTC COMMITTED batch; serial kokoro synth started (flock kokoro.lock, only-prefix 2026-08-27, log .tmp/synth27.log).

## 2026-08-27 day-23 closeout (synth → publish → live verify)

- SYNTH RUN 1: completed done=6 failed=0 — but ALL voice stamps silently skipped. ROOT CAUSE: I had prefilled 'Voice: pending' in front matter; synth_batch only stamps when no Voice: line exists, and 'pending' matched, so random draws went unrecorded while audio used them anyway. Deleted placeholders, deleted MP3s, re-ran (run 2: done=6 failed=0, 8.6-10.2 min). PITFALL RECORDED: never leave Voice: placeholder lines in new transcripts; omit the field entirely and let synth stamp it.
- Voice draw (run 2): bf_emma (VoiceMem), bf_isabella (FC), bf_lily (WarpSAC), bm_daniel (Agent-G2), bm_daniel (JIT), bf_isabella (D3-MOPD). Stamps committed be15832.
- build_rss.py needs explicit --episodes-dir episodes --site-dir site --config config.yaml (no defaults); publish.sh takes site-dir arg. Chain: build_rss OK 60 eps; publish OK, pushed gh-pages.
- ANOMALY: /workspace/.gh_token vanished between publish (which succeeded via askpass plumbing) and the Pages-builds API poll (401s). Public verification doesn't need it: ls-remote confirms remote gh-pages=4f8ae34; live feed poll1 already 60 items (propagation <25s).
- LIVE VERIFY: feed.xml 60 items (54+6); six 2026-08-27-*.mp3 all HTTP 200 (6.26-7.44 MB); site root 200; .nojekyll present in origin/gh-pages tree. Day-23 CLOSED end-to-end.
- NOTE: local origin/gh-pages ref was stale (d13dc14) after publish.sh's separate gh-pages checkout push; git fetch fixed view. Don't trust local remote-tracking refs post-publish.
- Cron e0646a456062 still enabled; next fire 2026-08-28 03:00 ET. Watch: if tomorrow also errors at startup, inspect job persistence/config.

## 2026-08-29 22:28 UTC migration handover prepared

- Audited live install for migration: python 3.11.15 venv (uv 0.11.1), kokoro 0.9.4 /
  misaki 0.9.4 / torch 2.13.0 (+cu130, TTS on CPU) / pymupdf 1.28.2 / pillow 12.3.0 /
  kittentts 0.8.1; espeak-ng + ffmpeg 7.1.5 system deps.
- Wrote requirements.txt (exact pins); wrote docs/MIGRATION.md (canonical migration +
  ops handover: STEP 0 dependency self-check, clone, venv, own credentials, MP3 restore
  from gh-pages, smoke tests, backfill, cron re-registration, carry-over rules).
- Migration-specific finding: cron missed Aug 28 AND Aug 29, but 08-29 is a Saturday and
  HF daily-papers snaps weekend requests back to the previous papers-day -> net backfill
  is exactly ONE slate, papers-day 2026-08-28. Duplicate-prevention rule documented.
- Portability fixes pushed so the new machine can run at any path: synth_kokoro.py +
  synth_batch.py now use tempfile.gettempdir(); publish.sh askpass defaults to repo root;
  config.yaml TTS_ENV demoted to a comment (no consumers); synth_queue.sh de-hardcoded;
  .gitignore mangled line repaired. Added scripts/nightly_prep.sh (unattended
  fetch+select for cron).
- Credential note: repo-root .gh_token (41 bytes, mode 600) is present and gitignored;
  the /workspace/.gh_token copy vanished on 08-27. New machine creates its OWN token +
  askpass (template in MIGRATION.md); values never transcribed.

## 2026-08-30 01:00-01:25 UTC — new-machine migration: env rebuilt + espeak-ng question resolved

- Audit (STEP 0) saved to ~/papercast-setup/.tmp/audit.txt: python3 3.12.3, ffmpeg 6.1.1,
  32 cores, 62 GiB RAM, 446 GB free, host tz = EDT. espeak-ng ABSENT; no passwordless
  sudo (user constraint: no sudo for this project).
- Zip landed WITHOUT `.git/` and `.venv/`. Restored `.git/` from a fresh network clone
  of agent-sora/papercast (top: 78f08d8; chain contains aca0271 as expected).
- Rebuilt venv with uv (python 3.12). `kittentts==0.8.1` does not exist on PyPI ->
  installed everything else from requirements.txt (legacy audition tools only lose
  kittentts, per handover note). Sanity imports OK (kokoro/pymupdf/yaml/PIL/misaki).
- RESEARCH (user asked: can kokoro run without espeak-ng; can the LLM supply phonemes?):
  - misaki EN G2P tiers: curated lexicon -> inline overrides `[Word](/ipa/)` ->
    espeak fallback. Overrides are honored verbatim (rating 5) — confirmed in
    misaki/en.py source AND end-to-end synthesis test.
  - espeakng_loader (pip dep of misaki[en]) bundles libespeak-ng.so IN THE VENV;
    EspeakFallback works on this host with NO system espeak-ng. KPipeline only
    drops OOD words if the fallback construction fails (pipeline.py try/except).
  - Wrote debugging/phoneme_override_test.py (docstring'd, re-runnable): asserts
    override IPA present in phoneme stream, OOD 'gptq' gets espeak phonemes,
    audio peak > 0.1. RESULT: PASS (peak 0.63, 9.8 s).
  - lint_script.py is compatible with the override syntax (no LaTeX/$/sci-notation
    patterns match it).
  - CAVEAT found: synth_kokoro.py's link-strip regex would delete override links
    before they reach G2P — must be fixed before adopting overrides in transcripts.
  - Decision pending with user: (a) keep espeak fallback as-is (no system pkg needed),
    (b) add a writer-side step where the LLM annotates known-tricky terms with
    inline phoneme overrides, (c) both. DESIGN.md updated with all of this.
- NEXT: git_askpass.sh + git identity; MP3 inventory check (60 expected); smoke
  tests; backfill papers-day 2026-08-28; register nightly cron.

## 2026-08-30 01:30-04:00 UTC — STEP 3/4/5 complete; day-24 backfill drafted

- STEP 3: .git_askpass.sh created at repo root (mode 700, reads .gh_token; token
  never echoed). ls-remote verified working via askpass. Git identity set to
  agent-sora <agent-sora@users.noreply.github.com> (7/8 prior commits); my first
  commit amended to that author.
- STEP 4: 60/60 episodes/*.mp3 present (426 MB) — matches live feed count 60.
  No gh-pages restore needed.
- STEP 5 smoke tests: (1) fetch --date 2026-08-29 snaps to papers-day 2026-08-28,
  23 papers cached; (2) lint on 2026-08-27 VoiceMem transcript: total FAILs: 0;
  (3) TTS end-to-end: the phoneme_override_test doubles as this — peak 0.63;
  (4) build_rss with explicit flags: 60 items in preview feed. All four pass.
- Clarify timed out (user AFK). Proceeded on defaults: keep espeak fallback as-is
  (documented in DESIGN.md), old-cron pausing flagged for patrick (cannot reach
  the old box from here).
- SLATE day-24 (papers-day 2026-08-28, true upvotes re-pulled from HF API):
  2608.25518 Agentic Game Dev/RLHEV (134), 2608.27456 UrbanGround (72),
  2608.27448 TTPO (69), 2608.26872 Self-OPD (69), 2608.27260 ACE survey (59),
  2608.15763 TaoLive HAT tech report (44). All 13 kept-candidate abstracts
  checked for the FM standing rule: none introduces a new foundation model
  (TaoLive is a deployed-system report, explicitly briefed as such).
- Meta+PDFs 6/6; text extracted pages 0-7 AND 8-15 per id (<id>.txt, <id>-more.txt):
  first-8-pages-only would have missed every benchmark section.
- INCIDENT — subagent writers all died: dispatched 6 parallel writer subagents;
  every one hit "Non-streaming API call timed out after 180s with no response"
  x3 retries on the long single-turn writing step; exit_reason=max_iterations,
  zero files written. Provider limitation (glm-5.3-flash via OpenCode Go), not a
  prompt problem. Fallback: wrote all six transcripts myself in this session.
  nightly cron prompt updated to forbid subagent long-form writing.
- Drafts iterated to lint "total FAILs: 0" x6 (word counts 1306-1538). Learned:
  FrontierChallenge precedent says team-byline + individual authors is honest
  (used for TaoLive: "TaoLive AIGC LLM Team, Yuhan Sun, Wenhao Lin"); UrbanGround
  PDF page 1 lists Meituan as affiliation 3 — fixed Labs field vs stale HF data.
- Built debugging/numeric_spotcheck.py: converts spoken number words back to
  digits and checks each against the paper text corpus (PDF extraction drops
  superscripts so "one trillion" matches "10^12" stored as 1012). Found+fixed
  its own decimal bug ("six five" must concatenate to 65, not sum to 11).
  All six transcripts: total unexplained: 0 (5 hand-verified ALLOWED artifacts:
  billions/trillions vs exponent forms, hyphenated "two-hundred-example",
  "810" spelled "eight hundred ten").
- Zip-carried working-tree regressions discarded: .gitignore and docs/MIGRATION.md
  held STALE pre-rewrite copies (their committed origin versions are newer and
  describe the actual zip transfer). .gitignore now also excludes .git_askpass.sh
  and .tmp/.
- Committed 59e503d: 6 transcripts + picks + requirements-resolved.txt
  (kittentts==0.8.1 unpinned: does not exist on PyPI; legacy-only dep).
- CRON registered: papercast-nightly (16fe9a62f8df), 03:00 America/New_York
  (host IS on EDT so schedule is literal), deliver=local. NOTE: this is a
  LOCAL-ONLY cron (CLI session): output saved but not delivered to any chat.
  It will fire unattended at 03:00 ET nightly. Prompt encodes: true-upvote
  re-pull, FM standing rule, 16-page text extraction, write-in-session (no
  subagent long-form), both gates, commit-before-synth, serial flock synth,
  explicit-flag build+publish, live curl verification, work log.
- OLD-BOX CRON (cron_e0646a456062, 03:00 ET): NOT verifiable from here. If it
  still fires, it will fetch "today" -> papers-day 2026-08-28 and try to publish
  a duplicate slate. PATRICK MUST pause/remove it on the old box before its next
  03:00 ET fire. New-machine duplicate guard: the nightly prompt's stop condition
  (episodes/<papers_date>-*.mp3 already exists) makes this machine skip, so worst
  case after tonight is only the old box duplicating, not both.
