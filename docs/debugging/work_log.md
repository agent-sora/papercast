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
