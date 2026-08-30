# Papercast — Migration & Operations Handover

**For:** the Hermes agent taking over on the new machine (user: `patrick`, home `/home/patrick`).
**Written:** 2026-08-29, from a live audit of the working install. Every command below was verified on the old box.
**Transfer medium:** patrick zipped the whole old project directory (including
`.git/`, `.venv/`, and all 60 published MP3s) and unzipped it at
`/home/patrick/papercast`. This doc rides along as `HANDOVER.md` and as
`docs/MIGRATION.md` inside the repo (identical content).

Papercast is a nightly ML-papers podcast: fetch the Hugging Face daily-papers
feed, select the top 6 papers by **true upvotes**, write one ~10-minute
implementation-focused episode per paper, synthesize with Kokoro-82M TTS (UK
voice pool), and publish RSS + site to GitHub Pages.

- Repo: `https://github.com/agent-sora/papercast` (branch `main` = source, `gh-pages` = live site)
- Site: `https://agent-sora.github.io/papercast/`
- Feed: `https://agent-sora.github.io/papercast/feed.xml` (60 items as of handover)
- Audio URLs: `https://agent-sora.github.io/papercast/episodes/YYYY-MM-DD-<arxiv_id>.mp3`
- State at handover: `main` pushed at `daa1fef`; gh-pages `4f8ae340`; day-23 (2026-08-27) batch fully live-verified. The zip was cut after `aca0271` (two doc/chore commits followed: `884bf82`, `daa1fef` — expect those on top, not `aca0271`).

The old machine is a **Docker sandbox**. Yours is not — paths differ, some
dependencies may already exist, and you run as a normal user. Work **only under
`/home/patrick/...`** — `$PC=/home/patrick/papercast` throughout this document.
NEVER set up in `/` or system directories. Package installs that need `sudo`
are fine, nothing else is.

---

## STEP 0 — Audit what already exists (do this FIRST)

Some of these may already exist on a non-sandbox machine. Check before
installing anything. Save the output to `~/papercast-setup/.tmp/audit.txt` so
the work log has it.

```bash
mkdir -p ~/papercast-setup/.tmp && cd ~/papercast-setup   # scratch dir; $PC is defined in STEP 1
{
  echo "== system =="
  command -v git python3 pip3 ffmpeg ffprobe espeak-ng flock curl || true
  git --version; python3 -V; ffmpeg -version 2>/dev/null | head -1
  espeak-ng --version 2>/dev/null || echo "espeak-ng MISSING"
  echo "== python imports =="
  python3 - <<'PY'
mods = ["kokoro", "torch", "numpy", "soundfile", "pymupdf", "requests",
        "yaml", "PIL", "onnxruntime", "kittentts", "misaki"]
import importlib
for m in mods:
    try:
        mod = importlib.import_module(m)
        print(f"{m:12s} OK  {getattr(mod,'__version__','')}")
    except Exception as e:
        print(f"{m:12s} MISSING ({type(e).__name__})")
PY
  echo "== network =="
  curl -sI https://github.com -o /dev/null -w 'github: %{http_code}\n'
  curl -sI https://huggingface.co -o /dev/null -w 'hf: %{http_code}\n'
  curl -sI https://agent-sora.github.io/papercast/feed.xml -o /dev/null -w 'site: %{http_code}\n'
  echo "== resources =="
  nproc; free -h | head -2; df -h "$HOME" | tail -1
  echo "tz: $(date +%Z%z)  (need 03:00 America/New_York = 07:00 UTC during EDT)"
} > .tmp/audit.txt 2>&1; cat .tmp/audit.txt
```

Decision rules from the audit:

| Finding | Action |
|---|---|
| Python < 3.11 | install 3.11+ (deadsnakes PPA on Ubuntu, or pyenv) |
| `espeak-ng` missing | `sudo apt install espeak-ng` (REQUIRED for TTS) |
| `ffmpeg`/`ffprobe` missing | `sudo apt install ffmpeg` (REQUIRED: feed durations) |
| imports missing | install via venv below — do NOT pip-install into system Python |
| `/tmp` mounted `noexec` | use `export TMPDIR=$PC/.tmp` everywhere (espeak-ng needs an **exec-able** TMPDIR) |
| < ~7 GB free in `$HOME` | warn user (venv ≈ 5 GB, MP3s ≈ 0.5 GB, HF model cache ≈ 1 GB) |
| synth needs ~2 GB free RAM, serial only | two concurrent TTS jobs OOM → silent audio |

## STEP 1 — You already have the code: the unzipped directory

Patrick zipped the **whole** old project directory — code, `.git/`, `.venv/`,
all 60 published MP3s, caches, everything — and unzipped it at `$HOME/papercast`.
There is **nothing to clone or download in STEP 1**. Verify what landed:

```bash
export PC="$HOME/papercast"        # = /home/patrick/papercast
cd "$PC"
git log --oneline -3               # expect daa1fef on top (then 884bf82, aca0271)
git status --porcelain | wc -l     # expect 0 — worktree clean
ls scripts/ | wc -l                # expect 14 scripts incl. nightly_prep.sh, publish.sh
ls episodes/*.md | wc -l           # expect 60 transcripts
ls episodes/*.mp3 2>/dev/null | wc -l   # 60 if MP3s survived, 0 if not (see STEP 3)
ls -d .venv .git .gh_token models 2>/dev/null
```

The last line tells you which heavy or hidden pieces survived the zip. Three
notes on what they mean:

- `.venv` present → the old Python environment traveled too. It is hardwired to
  the old sandbox (its `bin/python*` symlinks point into `/usr/local/bin`, and
  the old box was **aarch64**), so it will almost certainly **not** run on your
  machine. Treat it as a file inventory only and rebuild in STEP 2; delete it
  first (`rm -rf .venv`) if disk is tight.
- `.gh_token` present → the old credential traveled inside the repo dir. Same
  GitHub account, so it may still work — but prefer a fresh token (STEP 3).
- `episodes/*.mp3` count is 0 → MP3s were gitignored and did not survive;
  STEP 3 restores them from the `.git` history that traveled with you.

### What was taking the space on the old box (measured 2026-08-29)

The old directory was **6.5 GB** — that's why the zip is so large. Everything
below traveled; this table just explains the bulk and what is disposable now
that you have it:

| Path | Size | Verdict |
|---|---|---|
| `.venv/` | **5.0 GB** | Old torch+kokoro stack, hardwired to the old box. **Delete after STEP 2 rebuild.** |
| `.git/` | **589 MB** | **Keep.** History holds every MP3 ever published — STEP 4 extracts from here offline. |
| `episodes/feed/meta/` | **319 MB** | HF download cache (paper PDFs); re-fetches on demand. Deletable. |
| `episodes/*.mp3` | 460 MB | **Keep** if they survived the zip (check in STEP 1). |
| `models/` | 78 MB | Voice-pack data, needed. |
| `episodes/legacy-per-day/` | 70 MB | Optional. Old per-day RSS era. |
| `episodes/feed/text/` | 7 MB | Text cache; rebuilds from PDFs. Deletable. |
| everything else | < 10 MB | Needed. |

## STEP 2 — Python environment (test the traveled `.venv`, expect to rebuild)

The zip includes the old `.venv/` (5 GB). It was created with `uv` inside a
Docker sandbox and is hardwired to that box: every script in `.venv/bin/` has a
shebang and symlinks pointing at the old interpreter, and `.venv/pyvenv.cfg`
points `home` at the sandbox's Python 3.11. It may be broken or even
wrong-architecture. Try it first — it costs 30 seconds:

```bash
cd "$PC"
.venv/bin/python -c "import sys, torch, kokoro; print(sys.version); print('venv OK')"
```

- **Works?** Great, skip to the sanity check below.
- **Fails** (bad interpreter, missing module, `Exec format error` = wrong
  CPU arch): move it aside and rebuild from the audited pins:

```bash
mv .venv .venv-old                     # keep until the new one passes
python3 -m venv .venv                  # or: uv venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install pip -U           # only if pip is ancient
```

Delete `.venv-old/` once the rebuild passes the sanity check — it's 5 GB.

`requirements.txt` pins: `kokoro==0.9.4 misaki==0.9.4 kittentts==0.8.1
torch==2.13.0 numpy==2.4.6 onnxruntime==1.29.0 pymupdf==1.28.2 pyyaml==6.0.3
requests==2.34.2 soundfile==0.14.0 pillow==12.3.0`.

- The CPU torch wheel is fine (CUDA build was installed but TTS runs on CPU).
  If the pin won't resolve on your arch, install plain `torch` first, then the
  rest of the file.
- `kittentts`+`PIL`: PIL/pillow is a real production dep (`build_rss.py` draws
  the cover). `kittentts` is only used by the legacy `synthesize.py` and
  `audition_voices.py`; if it won't install, only those two tools are lost.
- `import pymupdf`, **not** `fitz` (1.28 renamed the import).
- First synthesis auto-downloads the Kokoro-82M weights (~350 MB) through the
  HF hub into `~/.cache/huggingface/`. If the box is offline, pre-fetch
  `hexgrad/Kokoro-82M`.

Sanity check (safe, no publish):

```bash
.venv/bin/python -c "from kokoro import KPipeline; import pymupdf, yaml, PIL; print('imports OK')"
```

## STEP 3 — Credentials (the token traveled; the askpass helper did NOT)

Two pieces live on the old box:

- `$PC/.gh_token` — repo root, mode 600, gitignored. It was inside the project
  dir, so **it traveled in the zip**. Recommended: ask patrick to rotate it
  (revoke the old one on GitHub, mint a fresh classic `repo`-scope token) since
  the zip crossed machines — then overwrite the file. If patrick prefers to
  keep using the traveled token, that is his call; it is his own account.

- `$PC/.git_askpass.sh` — it lived **outside** the repo on the old box, so it
  did NOT travel. Recreate it at repo root (`publish.sh` looks for
  `$ROOT/.git_askpass.sh`). Minimal shape — fill in the token yourself, never
  echo it:

```bash
cat > "$PC/.git_askpass.sh" <<'SH'
#!/bin/sh
case "$1" in
  Username*) echo "x-access-token" ;;
  Password*) cat "$PC/.gh_token" ;;
esac
SH
chmod 700 "$PC/.git_askpass.sh"
```

(`publish.sh` reads `TOKEN_FILE="$ROOT/.gh_token"` and
`ASKPASS="${GIT_ASKPASS:-$ROOT/.git_askpass.sh}"` where `ROOT` is the repo
root — both resolve automatically to your layout. The token must never appear
in command output, logs, or git remotes.)

Then set a git identity for `main` commits: `git config user.name` /
`user.email` — agree on one with `patrick`.

## STEP 4 — Verify the audio (MP3s should have traveled too)

The 60 published MP3s lived in `episodes/` (gitignored but present on disk), so
they **traveled in the zip**. `publish.sh` copies **every** `episodes/*.mp3` to
the site — if they ever go missing, your first publish **wipes the feed down to
just the new episodes** (from 60 items to ~6). So verify before anything else:

```bash
cd "$PC"
ls episodes/*.mp3 | wc -l                        # expect 60
du -ch episodes/*.mp3 | tail -1                  # expect ~461M total
```

**If fewer than 60:** the zip or the copy step dropped them. Extract from the
`.git` history that traveled with you (gh-pages branch, offline):

```bash
rm -rf .tmp/ghp && mkdir -p .tmp/ghp
git archive origin/gh-pages episodes | tar -x -C .tmp/ghp
cp -n .tmp/ghp/episodes/*.mp3 episodes/          # 60 files, ~460 MB
ls episodes/*.mp3 | wc -l                        # expect 60
rm -rf .tmp/ghp
```

(If `origin/gh-pages` is missing from the traveled `.git` too, fall back to the
network: `git fetch origin gh-pages` first, then repeat the two commands.)

Cross-check against the live feed count:
`curl -s https://agent-sora.github.io/papercast/feed.xml | grep -c '<item>'` → 60.

## STEP 5 — Smoke tests (all read-only for the live site)

```bash
cd "$PC"; export TMPDIR="$PC/.tmp"; mkdir -p .tmp

# 1. fetch works (2026-08-29 is a Saturday — watch it snap to papers-day 08-28)
.venv/bin/python scripts/fetch_papers.py --date 2026-08-29 --cache episodes/feed/ --no-print
grep -o '"papers_date": *"[^"]*"' episodes/feed/papers-2026-08-28.json | head -1

# 2. lint runner works on an existing transcript (expect "total FAILs: 0")
.venv/bin/python scripts/lint_script.py episodes/2026-08-27-2608.26005.md | tail -3

# 3. TTS works end-to-end (tiny text, ~1 min) — check the wav is non-silent
.venv/bin/python - <<'PY'
from kokoro import KPipeline
import soundfile as sf, numpy as np
p = KPipeline(lang_code='b')   # 'b' = British
audio = next(p("Migration smoke test.")).audio
sf.write(".tmp/smoke.wav", audio, 24000)
print("peak", float(np.abs(audio).max()), "secs", round(len(audio)/24000, 1))
PY
# peak must be > 0.1 — near-zero = silent-audio failure mode

# 4. site build works (writes .tmp/site_preview, does NOT publish)
.venv/bin/python scripts/build_rss.py --episodes-dir episodes --site-dir .tmp/site_preview --config config.yaml
grep -c '<item>' .tmp/site_preview/feed.xml   # expect 60
```

If all four pass, the migration is functionally complete. Do NOT run
`publish.sh` yet — first finish the backfill below so it ships in one deploy.

## STEP 6 — Backfill the missed nights

> **BEFORE BACKFILLING: get the old machine's cron paused or removed** (it is
> still registered: `cron_e0646a456062`, 03:00 ET). If it fires mid-backfill it
> will fetch "today" → snap back to the very papers-day you are covering and
> publish a duplicate slate. `patrick` pauses it on the old box.

The old cron died on the nights of **Aug 28 and Aug 29** (`last_status: error`,
no artifacts). But the HF daily-papers feed is not a calendar: a request for a
date with no new papers (weekends) **snaps back to the previous real
papers-day**. 2026-08-29 is a Saturday, so its fetch returns papers-day
**2026-08-28** — the same day Friday night's fire would have covered.

> **Net backfill = exactly ONE missing slate: papers-day 2026-08-28.**
> Do not publish anything dated 2026-08-29 — it would duplicate Friday's
> papers under a second date prefix.

Standing rule that prevents all duplicates: **after fetching, check
`ls episodes/<papers_date>-*.mp3`; if that papers-day already has episodes, or
the fetched slate is empty, log it and stop.** (This is also why there are no
weekend episodes historically — Mondays often snap back too.)

Full per-slate procedure (papers-day `D` = `2026-08-28`):

```bash
cd "$PC"; export TMPDIR="$PC/.tmp"
mkdir -p episodes/feed/picks episodes/feed/meta episodes/feed/text
D=2026-08-28   # the papers-day to backfill

# 1. fetch + shortlist
.venv/bin/python scripts/fetch_papers.py --date "$D" --cache episodes/feed/
.venv/bin/python scripts/select_papers.py --date "$D" --cache episodes/feed/ \
  --config config.yaml --json-out "episodes/feed/selected-$D.json"

# 2. pick exactly 6 by TRUE upvotes (highest first). STANDING RULE: always
#    include technical reports of new foundation models if present.
#    Write the arxiv ids, one per line:
printf '2608.XXXXX\n...' > "episodes/feed/picks/ids-$D.txt"

# 3. metadata + PDFs, then extract page text for grounding
.venv/bin/python scripts/paper_meta.py --ids-file "episodes/feed/picks/ids-$D.txt" \
  --cache-dir episodes/feed/meta
.venv/bin/python - <<'PY'
import pymupdf, pathlib
for pdf in pathlib.Path("episodes/feed/meta").glob("*.pdf"):
    txt = "\n".join(p.get_text() for p in pymupdf.open(pdf)[:8])
    pathlib.Path(f"episodes/feed/text/{pdf.stem}.txt").write_text(txt)
PY
```

4. **Draft** one transcript per paper: `episodes/D-<arxiv_id>.md`. Follow
   `docs/STYLE_GUIDE.md` exactly — it is authoritative: front-matter schema,
   cold-open formula, body **1,300–1,750 words**, speakable math, dispassionate
   tone, one episode per paper. Honest bylines: team-only authorship says so
   (e.g. "the Apodex Team") — never invent names. Public copy must NEVER
   contain the phrase "senior staff software engineer at a frontier lab".
   **Leave the `Voice:` front-matter line ABSENT** — a placeholder suppresses
   the auto-stamper and the episode ships without a recorded voice.
   Use a recent transcript (e.g. `episodes/2026-08-27-*.md`) as the template.

5. **Lint gate + numeric spot-check** (both must pass before synthesis):

```bash
.venv/bin/python scripts/lint_script.py episodes/$D-*.md   # require "total FAILs: 0"
```
   Then spot-check every number you speak (upvote counts, benchmark figures,
   parameter counts) against `episodes/feed/text/<id>.txt`. Numbers must trace
   to the paper.

6. **Synthesize — SERIAL ONLY.** One TTS job at a time or the box OOMs into
   silent audio. ~9–11 min/episode, ~1.9 GB RAM peak:

```bash
flock "$PC/.tmp/kokoro.lock" .venv/bin/python scripts/synth_batch.py --only-prefix "$D" \
  > ".tmp/synth-$D.log" 2>&1; tail -5 ".tmp/synth-$D.log"
```
   `synth_batch.py` auto-stamps a random voice from the UK pool
   (`bf_alice bf_emma bf_isabella bf_lily bm_daniel bm_fable bm_george bm_lewis`)
   into the front matter and sets `TMPDIR` + `OMP_NUM_THREADS=1` itself.

7. **Publish** (explicit flags are mandatory — positional defaults broke once):

```bash
.venv/bin/python scripts/build_rss.py --episodes-dir episodes --site-dir site --config config.yaml
bash scripts/publish.sh site
```

8. **Verify live** (Pages takes 1–5 min; poll, don't assume):

```bash
curl -s https://agent-sora.github.io/papercast/feed.xml | grep -c '<item>'   # 60 → 66
for id in $(cat "episodes/feed/picks/ids-$D.txt"); do
  curl -s -o /dev/null -w "%{http_code} $id\n" \
    "https://agent-sora.github.io/papercast/episodes/$D-$id.mp3"              # expect 200 ×6
done
git fetch origin gh-pages && git ls-tree origin/gh-pages --name-only | grep -x '.nojekyll'
```
   (`.nojekyll` is recreated by every `publish.sh` run; verify anyway. Note the
   gh-pages tracking ref goes stale after each publish — `git fetch` first.)

9. **Record + push:** append a timestamped entry to `docs/debugging/work_log.md`,
   commit transcripts + feed artifacts to `main`, push. Committing/pushing
   after every batch is the recovery mechanism for exactly the failure that
   caused this backfill.

## STEP 7 — Schedule the nightly cron on THIS machine

Old schedule: **03:00 America/New_York** (= 07:00 UTC during EDT). Register a
new job with the cronjob tool on your host. Compute the wall-clock equivalent
of 03:00 ET for the host's timezone first (`timedatectl`, or `TZ=America/New_York date`).

Job parameters:

- **name:** `papercast-nightly`
- **schedule:** daily at the computed time (cron syntax, e.g. `0 3 * * *` if the host is on ET)
- **deliver:** origin (default)
- **prompt** (self-contained — cron sessions start with no context):

```
You are the Papercast night-shift agent. Repo: /home/patrick/papercast ($PC).
Run: cd $PC && export TMPDIR=$PC/.tmp && bash scripts/nightly_prep.sh
Read the printed shortlist (episodes/feed/selected-<papers_date>.json).
STOP CONDITIONS — if the shortlist is empty, or episodes/<papers_date>-*.mp3
already exists, or fetch failed, log to docs/debugging/work_log.md and stop.
Otherwise do the full batch for papers_date, exactly as documented in
docs/MIGRATION.md STEP 6: pick 6 by true upvotes (STANDING RULE: always
include technical reports of new foundation models), paper_meta.py, pymupdf
text extraction, draft per docs/STYLE_GUIDE.md (1300-1750 words each, Voice:
line ABSENT), lint to 0 FAILs, numeric spot-check vs episodes/feed/text/,
serial synth under flock .tmp/kokoro.lock, build_rss.py with explicit flags,
publish.sh site, verify feed item count and 6 MP3 HTTP 200s + .nojekyll,
append work log, commit and push main.
```

Notes: the repo now ships `scripts/nightly_prep.sh` (added 2026-08-29) which
does the unattended fetch+select so the fire can start at pick review.

**Reliability history you inherit** — treat the old job's failures as the norm
to design against: 08-26 sandbox restart killed a batch mid-synthesis; 08-27,
08-28, 08-29 fires errored with no artifacts. Therefore: **trust only what's on
disk** (`episodes/`, `episodes/feed/`), never a cron's claimed success; verify
the live feed after every batch; and when a night is missed, backfill with
STEP 6 rather than waiting for it to self-heal.

## STEP 8 — Retirement of the old machine

The old cron (`cron_e0646a456062`, 03:00 ET) should already be paused (STEP 6
warning). Once your first full night fires clean and the backfill is live, it
can be removed there, and the old `/workspace` copy becomes a backup, not the
source of truth. `patrick` handles the old box.

---

## Rules that MUST carry over (learned the hard way)

1. `docs/STYLE_GUIDE.md` is authoritative for transcripts; lint gate is
   **hard**: `total FAILs: 0` before any synthesis.
2. Numeric spot-check against extracted paper text before synthesis — every
   spoken number must trace to the paper.
3. One episode per paper, ~10 min; body 1,300–1,750 words; speakable math.
4. Standing rule: technical reports of new foundation models are ALWAYS
   included when present in the daily papers (check every slate).
5. Honest bylines; team-only authorship is stated as such; never fabricate
   names. Public copy never contains "senior staff software engineer at a
   frontier lab".
6. Leave `Voice:` ABSENT in front matter — the synth auto-stamper skips
   episodes that carry a placeholder, and you'll ship a voiceless episode.
7. Serial TTS only (`flock .tmp/kokoro.lock`); concurrent Kokoro OOMs into
   silent audio. Check the audio peak if in doubt.
8. Never publish without first verifying the audio inventory (STEP 4).
9. After every publish, `git fetch origin gh-pages` before inspecting it.
10. Record every incident in `docs/debugging/work_log.md` — it is the project's
    memory across machines.

## Known pitfalls (encountered on the old box)

- `pymupdf` imports as `import pymupdf` (not `fitz`).
- `grep` on extracted PDF text needs `grep -a` sometimes; prefer Python.
- espeak-ng needs an **exec-able** TMPDIR; if `/tmp` is noexec use `$PC/.tmp`.
- HF fetch is cache-first per papers-day; use `--force` to re-pull an updated slate.
- `select_papers.py` drops candidates for cause (control layers etc.) and logs
  the reason — read its stderr before overriding the shortlist.
- Lint cold-open em-dash parsing quirk: if a correct cold open fails lint,
  check how the linter tokenizes the first sentence before rewording.
- Build RSS with explicit `--episodes-dir/--site-dir/--config` flags, always.
- Publish chain order: `build_rss.py` → `publish.sh site`; verify with curl,
  never by trusting exit codes alone.

## File map

```
$PC/
├── config.yaml              # GH_REPO, voice pool, selector config (TTS_ENV is a legacy note)
├── requirements.txt         # exact audited pins
├── .gh_token                # traveled in zip; rotate via patrick (mode 600)
├── .git_askpass.sh          # YOUR askpass (mode 700, not in repo)  [create]
├── .tmp/                    # locks, logs, evidence dir
├── episodes/                # YYYY-MM-DD-<arxiv_id>.md + .mp3 (60 mp3 traveled; verify STEP 4)
│   └── feed/                # papers-<d>.json, selected-<d>.json, picks/ids-<d>.txt,
│                            #   meta/<id>.json+.pdf, text/<id>.txt
├── site/                    # generated by build_rss.py (gitignored)
├── docs/STYLE_GUIDE.md      # transcript law
├── docs/MIGRATION.md        # this document
├── docs/debugging/work_log.md
└── scripts/                 # fetch_papers, select_papers, paper_meta, synth_batch,
                             #   synth_kokoro, build_rss, publish.sh, lint_script,
                             #   nightly_prep, make_cover, publish_watch, synthesize
                             #   (legacy), synth_queue.sh (legacy), audition_voices
```
