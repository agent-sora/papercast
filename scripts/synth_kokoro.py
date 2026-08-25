#!/usr/bin/env python3
"""Kokoro-82M TTS synthesizer for Agent-Sora Daily (voice: bf_isabella).

Reads a markdown transcript (## headings become pauses, paragraphs are spoken),
splits it into sentence-bounded chunks, synthesizes each with kokoro, and
concatenates to a single mp3 via ffmpeg.

Usage:
  synth_kokoro.py --transcript episodes/2026-08-21-foo.md --out episodes/x.mp3
"""
import argparse, os, re, subprocess, sys, tempfile, time

CHUNK_MAX = 420          # chars per synthesis chunk
SR = 24000               # kokoro output sample rate

def load_transcript(path):
    """Return plain spoken text: strip YAML front matter, headings, links."""
    lines = open(path, encoding="utf-8").read().splitlines()
    if lines and lines[0].strip() == "---":          # YAML front matter block
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                lines = lines[i + 1:]
                break
    out = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith("```"):
            continue
        if s.startswith("#"):            # headings -> short pause marker
            out.append("")
            continue
        s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
        s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
        s = re.sub(r"\*\*?", "", s)
        out.append(s)
    return "\n".join(out)

def split_chunks(text):
    """Sentence-bounded chunks <= CHUNK_MAX chars."""
    text = re.sub(r"\n{2,}", "\n", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, cur = [], ""
    for sent in sentences:
        while len(sent) > CHUNK_MAX:     # pathological very-long sentence
            cut = sent.rfind(",", 0, CHUNK_MAX)
            cut = cut if cut > CHUNK_MAX // 2 else CHUNK_MAX
            chunks.append(sent[:cut].strip()); sent = sent[cut:].strip()
        if len(cur) + len(sent) + 1 > CHUNK_MAX and cur:
            chunks.append(cur.strip()); cur = sent
        else:
            cur = f"{cur} {sent}".strip()
    if cur.strip():
        chunks.append(cur.strip())
    return [c for c in chunks if c]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--speed", type=float, default=1.0)
    args = ap.parse_args()

    import torch
    torch.set_num_threads(4)
    from kokoro import KPipeline
    pipe = KPipeline(lang_code="a")                      # American English
    text = load_transcript(args.transcript)
    chunks = split_chunks(text)
    print(f"# {len(chunks)} chunks ({len(text)} chars)", flush=True)

    import numpy as np, soundfile as sf
    t0 = time.time()
    pieces, total_samples = [], 0
    chunk_failures = 0
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR", "/tmp")) as td:
        wav_paths = []
        for i, ch in enumerate(chunks, 1):
            try:
                gen = list(pipe(ch, voice="bf_isabella", speed=args.speed))
                audio = np.concatenate([g.audio for g in gen if g.audio is not None])
            except Exception as e:
                print(f"[warn] chunk {i} failed ({e}); skipping", flush=True)
                chunk_failures += 1
                audio = np.zeros(int(SR * 0.4), dtype=np.float32)   # breath gap
            p = os.path.join(td, f"{i:04d}.wav")
            sf.write(p, audio, SR)
            wav_paths.append(p)
            total_samples += len(audio)
            if i % 10 == 0 or i == len(chunks):
                done = total_samples / SR
                rate = done / (time.time() - t0)
                print(f"  {i}/{len(chunks)}  {done/60:.1f}s audio "
                      f"({rate:.2f}x realtime)", flush=True)
        # concat with small silence between chunks for natural pacing
        list_file = os.path.join(td, "list.txt")
        gap = os.path.join(td, "gap.wav")
        sf.write(gap, np.zeros(int(SR * 0.25), dtype=np.float32), SR)
        with open(list_file, "w") as f:
            for j, p in enumerate(wav_paths):
                f.write(f"file '{p}'\n")
                if j != len(wav_paths) - 1:
                    f.write(f"file '{gap}'\n")
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        # write to a temp name then atomically rename, so watchers/publishers
        # never observe a half-written mp3
        part_out = args.out + ".part"
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                        "-i", list_file,
                        "-codec:a", "libmp3lame", "-b:a", "96k",
                        part_out], check=True, capture_output=True)
        os.replace(part_out, args.out)
    secs = total_samples / SR
    if chunk_failures > max(1, len(chunks) // 3) or secs < 60:
        # degenerate run (e.g. GPU/CPU pressure): refuse to ship a mostly-silent
        # episode — the batch driver will report FAIL and a later pass retries
        print(f"ABORT: {chunk_failures}/{len(chunks)} chunks failed, only "
              f"{secs:.0f}s audio produced", flush=True)
        return 2
    print(f"WROTE {args.out}: {secs:.0f}s ({secs/60:.1f} min), "
          f"{time.time()-t0:.0f}s wall", flush=True)

if __name__ == "__main__":
    main()
