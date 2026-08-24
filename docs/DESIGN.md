# Agent-Sora Podcast — Design Document

Status: IN PROGRESS (voice selected; pipeline + GitHub setup pending)
Last updated: 2026-08-24

## Purpose

A daily podcast that turns that day's interesting HuggingFace papers into a
~30-minute technical briefing for a senior staff software engineer, read by a
chosen TTS voice, published as audio + an RSS feed via GitHub Pages,
one self-contained directory.

## Source & topic scope (user-defined)

- Feed: `https://huggingface.co/papers` (HF daily papers).
- Include topics:
  - RL algorithms applied to **text / agentic** work (not image/video).
  - Agent self-improvement.
  - AI music generation (audio, not video; broadened training-data preference
    applies to the *podcast* material, not selection scope).
  - AI for finance / econometrics / statistical arbitrage.
  - LoRA/PEFT methods **only** for text/reasoning/agentic uses.
- Exclude: image/video papers; LoRA/PEFT applied to image/video.
- Encoded in `config.yaml` under `TOPIC_INCLUDE_FLAVORS` / `TOPIC_EXCLUDE`.

## Voice / TTS

- Biggest model = `kitten-tts-mini-0.8` (80M params); synthesis on CPU.
- Accent requirement: **Received Pronunciation only**.
- No voice-accent metadata in KittenTTS, so the pick was made **by ear** from an
  8-voice audition (`scripts/audition_voices.py`, clips in `audition/`).
- **DECISION (2026-08-24): voice = ROSIE.**
- Speed: Rosie RTF ≈1.15×real-time on this box ⇒ ~35 min to synth a 30-min ep;
  fine for a nightly background job.
- Sample rate 24000 Hz (fixed by `generate()`; verified bug fix in
  `audition_voices.py` — `generate()` returns a single waveform ndarray, no sr).

## Architecture

```
config.yaml               # all decisions (voice, topics, RSS)
scripts/
  fetch_papers.py        # get HF daily papers (huggingface.co/papers)
  select_papers.py       # apply topic rules -> keep/drop
  script_gen.py          # EPISODE_TARGET_MINUTES technical summary
  synthesize.py          # TTS Rosie -> mp3 (kitten-tts-mini-0.8, CPU)
  build_rss.py           # build feed.xml per episode
  publish.py             # push site + RSS to GitHub Pages
  audition_voices.py     # (done) voice audition + RTF benchmark
site/                    # generated static site + feed.xml + audio/
cron: nightly job        # fetch -> select -> script -> synth -> publish
```

## Deliverables still to do

1. gh-setup — create repo (agent-sora), enable Pages, verify token scopes.
2. pipeline — write the pipeline stages above.
3. e2e-test — run one full day end-to-end.
4. backfill-scripts — produce paper-selection + episode scripts for 6 more days.
5. synthesize — synth all 7 backfill episodes to mp3.
6. publish — publish site + RSS, verify live URLs.
7. cron — save reusable skill + create nightly cronjob.
8. report — feed URL, subscription info, token-rotation reminder.

## Alternatives considered

- Smaller/faster models (mini-0.4 etc.) rejected: user explicitly wants biggest
  since he listens to it. Faster RTF (Luna 0.76) noted but voice quality wins.
- Non-RP accents rejected by user (RP only, verbatim).
- KittenTTS over cloud TTS (OpenAI/ElevenLabs) — no new subscriptions per user.