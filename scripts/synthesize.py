#!/usr/bin/env python3
"""Synthesize an episode transcript (markdown) to an mp3 with KittenTTS / Rosie.

Reads a markdown transcript with `## Section` headings and paragraphs, speaks it
with the configured KittenTTS model+voice, and concatenates chunked audio with a
short gap into one mp3. Chunking keeps each individual synth call bounded so a
30-minute episode never runs away in one call.

Transcript conventions (used by the podcast author):
  - `## Heading`   -> spoken as a section marker, e.g. "Second paper: ..."
  - plain lines    -> paragraph text, spoken verbatim (markdown symbols stripped)
  - `---` / blank  -> paragraph separators

Usage:
    python scripts/synthesize.py --transcript episodes/2026-08-21.md \
        --out episodes/2026-08-21.mp3 [--voice Rosie --model KittenML/kitten-tts-mini-0.8]
"""
import argparse
import json
import os
import re
import sys
import time

import numpy as np
import soundfile as sf

from kittentts import KittenTTS

SR = 24000  # KittenTTS fixed sample rate
GAP_S = 0.30  # ~300ms natural pause between chunks


def load_transcript(path: str) -> list[tuple[str, str]]:
    """Return [(kind, text), ...] where kind in {'heading','para'}."""
    out = []
    with open(path) as f:
        for raw in f:
            line = raw.rstrip("\n")
            if line.startswith("#"):
                heading = line.lstrip("#").strip()
                if heading:
                    out.append(("heading", heading))
            elif line.strip().startswith("---"):
                continue
            elif line.strip():
                out.append(("para", line.strip()))
    return out


def tts_friendly(text: str) -> str:
    """Strip markdown symbols so the TTS reads clean prose."""
    t = re.sub(r"[*_`>|]", "", text)
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)  # links -> label
    t = re.sub(r"\s+", " ", t).strip()
    return t


def split_long(text: str, max_chars: int = 2200) -> list[str]:
    """Split on sentence boundaries so each synth call is bounded."""
    if len(text) <= max_chars:
        return [text]
    parts = []
    for sent in re.split(r"(?<=[.!?])\s+", text):
        if not sent.strip():
            continue
        if parts and len(parts[-1]) + len(sent) + 1 <= max_chars:
            parts[-1] += " " + sent
        else:
            parts.append(sent)
    return [p for p in parts if p.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice", default="Rosie")
    ap.add_argument("--model", default="KittenML/kitten-tts-mini-0.8")
    ap.add_argument("--manifest", default=None, help="write per-chunk stats JSON")
    args = ap.parse_args()

    if not os.environ.get("TMPDIR"):
        # espeak-ng needs an exec-able dir; default /workspace/.tmp if set by parent
        pass

    chunks = load_transcript(args.transcript)
    if not chunks:
        print("!! empty transcript", file=sys.stderr)
        return 2
    print(f"# {len(chunks)} chunks ({sum(len(c[1]) for c in chunks)} chars)", file=sys.stderr)

    t0 = time.monotonic()
    tts = KittenTTS(args.model)

    audio_parts: list[np.ndarray] = []
    stats = []
    for i, (kind, text) in enumerate(chunks):
        clean = tts_friendly(text)
        if kind == "heading":
            clean = f"{clean}."
        for j, piece in enumerate(split_long(clean)):
            ts = time.monotonic()
            wave = tts.generate(piece, voice=args.voice)
            wall = time.monotonic() - ts
            dur = len(wave) / SR
            audio_parts.append(wave.astype(np.float32))
            audio_parts.append(np.zeros(int(GAP_S * SR), dtype=np.float32))
            stats.append({"i": i, "piece": j, "chars": len(piece),
                          "synth_s": round(wall, 2), "dur_s": round(dur, 2),
                          "rtf": round(wall / dur, 2) if dur else None})
            if (i + 1) % 10 == 0:
                print(f"  {i+1}/{len(chunks)} ...", file=sys.stderr)

    full = np.concatenate(audio_parts) if audio_parts else np.zeros(0)
    total_dur = len(full) / SR
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    wav_tmp = args.out.rsplit(".", 1)[0] + ".wav.tmp.wav"
    sf.write(wav_tmp, full, SR)
    os.system(f'ffmpeg -y -loglevel error -i "{wav_tmp}" -b:a 192k "{args.out}"')
    os.remove(wav_tmp)

    wall = time.monotonic() - t0
    print(f"# done: {total_dur:.1f}s audio in {wall:.1f}s wall "
          f"({len(audio_parts)//2} pieces) -> {args.out}", file=sys.stderr)
    if args.manifest:
        with open(args.manifest, "w") as f:
            json.dump({"audio_s": round(total_dur, 2), "wall_s": round(wall, 2),
                       "pieces": stats}, f, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())