#!/usr/bin/env python3
"""Batch-synthesize episode mp3s from transcripts (serial, OOM-safe).

Finds episodes/YYYY-MM-DD-<arxiv_id>.md transcripts, strips front matter, and
synthesizes each to a sibling .mp3 by invoking scripts/synth_kokoro.py as a
SUBPROCESS (one per episode) so a hung/OOM-killed kokoro run never poisons the
batch — memory is fully released between episodes. Skips mp3s that already
exist with size > 10 KB (resumable). Sandbox constraint: NEVER run two kokoro
processes concurrently (cgroup OOM-kill); this script is strictly serial.

Usage:
    python scripts/synth_batch.py [--episodes-dir episodes] [--only-prefix 2026-08-13]
Prints one PROGRESS line per episode and SYNTH_BATCH_DONE <n> at the end.
"""
import argparse
import os
import random
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lint_script import check_file  # noqa: E402
FNAME_RE = re.compile(r"(\d{4}-\d{2}-\d{2})-(\d{4}\.\d{4,5})\.md$")


def body_without_front_matter(md_path: str) -> str:
    with open(md_path, encoding="utf-8") as f:
        text = f.read()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip() + "\n"
    return text.strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes-dir", default="episodes")
    ap.add_argument("--only-prefix", default=None,
                    help="e.g. 2026-08-13 to synthesize just that day")
    ap.add_argument("--seed", type=int, default=None,
                    help="reproducible voice draws (default: true random)")
    args = ap.parse_args()

    md_files = sorted(
        f for f in os.listdir(args.episodes_dir)
        if FNAME_RE.search(f)
        and (args.only_prefix is None or f.startswith(args.only_prefix))
    )
    if not md_files:
        print("NO_TRANSCRIPTS_MATCHED", flush=True)
        return 1

    done = failed = skipped = 0
    rng = random.Random(args.seed)
    from synth_kokoro import VOICES
    for i, name in enumerate(md_files, 1):
        stem = name[:-3]
        out_mp3 = os.path.join(args.episodes_dir, stem + ".mp3")
        if os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 10240 \
                and os.path.getmtime(out_mp3) >= os.path.getmtime(
                    os.path.join(args.episodes_dir, name)):
            skipped += 1
            print(f"[{i}/{len(md_files)}] SKIP {stem} (exists)", flush=True)
            continue

        tmp_txt = os.path.join("/workspace/.tmp", stem + ".tts.txt")
        os.makedirs(os.path.dirname(tmp_txt), exist_ok=True)
        md_path = os.path.join(args.episodes_dir, name)
        fails, _, wc = check_file(md_path)
        if fails:
            print(f"[{i}/{len(md_files)}] LINT-FAIL {stem} ({wc}w): "
                  f"{fails[0]}", flush=True)
            failed += 1
            continue
        # one uniform-random UK voice per episode (re-drawn only on re-synth)
        voice = rng.choice(VOICES)
        with open(md_path, encoding="utf-8") as f:
            md_text = f.read()
        m = re.match(r"^---\n(.*?\n)---\n", md_text, re.S)
        if m and not re.search(r"^Voice:", m.group(1), re.M):
            fm_new = re.sub(r"\n---\n$", f"\nVoice: {voice}\n---\n",
                            m.group(0))
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(fm_new + md_text[len(m.group(0)):])
        elif not m:
            voice = "bf_isabella"  # no front matter; keep legacy default
        with open(tmp_txt, "w", encoding="utf-8") as f:
            f.write(body_without_front_matter(md_path))

        cmd = [sys.executable, os.path.join(HERE, "synth_kokoro.py"),
               "--transcript", tmp_txt, "--out", out_mp3,
               "--voice", voice]
        env = dict(os.environ, TMPDIR="/workspace/.tmp", OMP_NUM_THREADS="1")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=3600, env=env)
            ok = r.returncode == 0 and os.path.exists(out_mp3) \
                and os.path.getsize(out_mp3) > 10240
            out_lines = [l for l in (r.stdout or "").splitlines()
                         if l.strip()]
            tail = out_lines[-1:] or [""]
            warns = [l for l in out_lines if "[warn]" in l][:3]
            print(f"[{i}/{len(md_files)}] {'OK ' if ok else 'FAIL'} {stem} "
                  f"{tail[0][:80]}", flush=True)
            for w in warns:
                print(f"    {w[:160]}", flush=True)
            if not ok and r.stderr:
                print(f"    stderr: {r.stderr.strip().splitlines()[-1][:200]}",
                      flush=True)
            done += ok
            failed += not ok
        except subprocess.TimeoutExpired:
            failed += 1
            print(f"[{i}/{len(md_files)}] TIMEOUT {stem}", flush=True)

    print(f"SYNTH_BATCH_DONE done={done} failed={failed} skipped={skipped}",
          flush=True)
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
