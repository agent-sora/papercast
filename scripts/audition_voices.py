#!/usr/bin/env python3
"""Audition every KittenTTS 0.8 voice on the biggest model (kitten-tts-mini-0.8)
and report a CPU speed benchmark (RTF = synth_time / audio_duration) per voice.

Used to pick the Received-Pronunciation (RP) British voice: KittenML ships the 8
alias names with no accent metadata, so accent judgment must be done by ear on
real clips. Writes an `audition/<voice>.wav/.mp3` per voice plus a JSON manifest.

Usage:
    /workspace/podcast/.venv/bin/python scripts/audition_voices.py [--text "..."] [--out DIR]
"""
import argparse
import json
import os
import time

import soundfile as sf

from kittentts import KittenTTS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = "KittenML/kitten-tts-mini-0.8"
VOICES = ["Bella", "Jasper", "Luna", "Bruno", "Rosie", "Hugo", "Kiki", "Leo"]

DEFAULT_TEXT = (
    "Hello and welcome to Papers Daily. Today we will look at reinforcement learning "
    "algorithms for language agents, and a new method for low rank adaptation in "
    "reasoning models. This clip lets you judge the accent."
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default=DEFAULT_TEXT)
    ap.add_argument("--out", default=os.path.join(ROOT, "audition"))
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    tts = KittenTTS(MODEL)

    SR = 24000  # KittenTTS fixed sample rate (see generate_to_file default)

    manifest = {}
    for voice in VOICES:
        t0 = time.monotonic()
        audio = tts.generate(args.text, voice=voice)
        wall = time.monotonic() - t0
        sr = SR
        duration = len(audio) / sr
        rtf = wall / duration if duration else float("nan")

        base = os.path.join(args.out, voice)
        sf.write(base + ".wav", audio, sr)
        os.system(f'ffmpeg -y -loglevel error -i "{base}.wav" -b:a 192k "{base}.mp3"')

        manifest[voice] = {
            "duration_s": round(duration, 3),
            "synth_s": round(wall, 3),
            "rtf": round(rtf, 3),
            "speed_mult": round(1.0 / rtf, 3),
            "wav": base + ".wav",
            "mp3": base + ".mp3",
        }
        print(f"{voice:8s} len={duration:6.2f}s synth={wall:6.2f}s "
              f"rtf={rtf:5.2f}x ({1.0/rtf:5.2f}x realtime)")

    with open(os.path.join(args.out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print("\nWrote", len(manifest), "clips + manifest.json to", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())