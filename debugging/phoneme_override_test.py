#!/usr/bin/env python3
"""Verify Kokoro/misaki pronunciation behavior WITHOUT a system espeak-ng binary.

Background (2026-08-29, new-machine migration):
  misaki's English G2P has three tiers:
    1. curated lexicon (spaCy + num2words)
    2. inline overrides:  [Word](/ipa ˈphoːnɪmz/)  in the input text
    3. espeak fallback    (misaki.espeak.EspeakFallback -> phonemizer ->
                           espeakng_loader, which BUNDLES libespeak-ng.so in
                           the venv — no system package required)
  KPipeline (kokoro/pipeline.py) tries to build the espeak fallback and, on
  failure, degrades to *silently dropping* OOD words (unk='').

This test proves, on a host with NO espeak-ng installed:
  1. Inline phoneme overrides are honored verbatim by the G2P stage
     (the returned phoneme stream contains exactly the override IPA).
  2. The espeak fallback still works for out-of-dictionary words
     (espeakng_loader's bundled .so is used, not a system binary).
  3. The synthesized audio is non-silent (peak amplitude sanity check —
     the known silent-audio failure mode of overloaded TTS runs).

Usage:
  cd <repo root>
  .venv/bin/python debugging/phoneme_override_test.py

Exits 0 if all checks pass, 1 otherwise. Safe to re-run at any time;
synthesizes ~10 s of audio.
"""
import os
import sys
import tempfile

import numpy as np
import soundfile as sf

# espeak/phonemizer spawn temp files; keep them in the repo's .tmp
os.environ.setdefault("TMPDIR", os.path.join(os.path.dirname(__file__), "..", ".tmp"))
os.makedirs(os.environ["TMPDIR"], exist_ok=True)
os.environ.setdefault("OMP_NUM_THREADS", "1")

OVERRIDES = {
    "Kokoro": "kˈOkəɹO",
    "Qwen": "kwɛn",
    "LoRA": "ˈlɔːɹə",
    "GPTQ": "ˈdʒɛptkjuː",
}
TEXT = ("[Kokoro](/{kokoro}/) was trained on phoneme labels. "
        "The [Qwen](/{qwen}/) model uses [LoRA](/{lora}/) adapters "
        "and [GPTQ](/{gptq}/) quantization. "
        "Plain out-of-dictionary fallback word: gptq.").format(
    kokoro=OVERRIDES["Kokoro"], qwen=OVERRIDES["Qwen"],
    lora=OVERRIDES["LoRA"], gptq=OVERRIDES["GPTQ"])

EXPECTED_FALLBACK = "ʤˌiːpˌiːtˌiːkjˈuː"   # what misaki.espeak emits for 'gptq' (en-gb)


def main() -> int:
    from kokoro import KPipeline

    pipe = KPipeline(lang_code="b")   # British English, matches the show's voice pool
    ok = True

    for i, (gs, ps, audio) in enumerate(pipe(TEXT, voice="bm_daniel")):
        gs = str(gs)
        ps = str(ps)
        audio = np.asarray(audio, dtype=np.float32) if audio is not None \
            else np.zeros(0, dtype=np.float32)
        print(f"chunk {i}: gs={gs!r}\n         ps={ps!r}")
        wav = os.path.join(os.environ["TMPDIR"], f"phon_override_test_{i}.wav")
        sf.write(wav, audio, 24000)
        peak = float(np.abs(audio).max()) if len(audio) else 0.0
        print(f"         peak={peak:.4f} secs={len(audio) / 24000:.1f}")
        if peak < 0.1:
            print(f"FAIL: chunk {i} is silent (peak {peak})")
            ok = False
        # 1. overrides honored verbatim
        for word, ipa in OVERRIDES.items():
            if ipa not in ps:
                print(f"FAIL: override for {word!r} ({ipa}) not in phoneme stream")
                ok = False
        # 2. espeak fallback active without system binary
        if EXPECTED_FALLBACK not in ps:
            print("FAIL: OOD word 'gptq' missing espeak-fallback phonemes "
                  "(OOD words would be dropped, not pronounced)")
            ok = False

    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
