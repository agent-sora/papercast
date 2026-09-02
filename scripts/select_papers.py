#!/usr/bin/env python3
"""Filter a day's HuggingFace papers by the user's topic rules from config.yaml.

The user's rules (encoded as TOPIC_INCLUDE_FLAVORS / TOPIC_EXCLUDE):
  INCLUDE:
    - rl_algorithms_text_agentic  RL algo work applied to text/agentic tasks
    - agent_self_improvement      agents that improve themselves (reflexion etc.)
    - ai_music_generation         audio / music generation (audio, not video)
    - ai_finance_econometrics     finance / econometrics / statistical arb
    - lora_peft_text_only         LoRA/PEFT for text / reasoning / agentic ONLY
    - reasoning_model_topology    topological changes to reasoning LMs: looping,
                                  recurrent depth, alternative attention
                                  (user standing rule 2026-09-02)
  EXCLUDE (hard):
    - image_or_video              any paper substantially about vision/video/media
    - lora_peft_image_video       LoRA/PEFT applied to image/video

Heuristic layer: keyword scoring per flavor, with a hard image/video veto. It is
deliberately NOT a final answer — it returns a ranked shortlist WITH the reasons
and per-paper veto notes so the podcast author (the agent writing the episode)
can make the final call on ambiguous papers. Output is one JSON line per paper
plus a short human-readable list on stderr.

Usage:
    python scripts/select_papers.py --date 2026-08-21 \
        --cache episodes/feed/ --config config.yaml
"""
import argparse
import json
import os
import re
import sys

import yaml

# --- keyword lexicons -------------------------------------------------- #
# Each flavor: list of regex fragments, case-insensitive, OR'd together.
FLAVORS = {
    "rl_algorithms_text_agentic": [
        r"reinforcement learning", r"\brl\b", r"GRPO", r"PPO", r"DPO", r"RLHF",
        r"reward model", r"policy gradient", r"credit assignment", r"off-policy",
        r"\bon-policy", r"multi-agent reinfor",
    ],
    "agent_self_improvement": [
        r"self-improv", r"self-correct", r"reflexion",
        r"self-refin", r"self-train", r"self-play", r"agent", r"tool use",
        r"tool-use", r"iterative", r"planning", r"world model", r"reasoning agent",
        r"code agent", r"coding agents?", r"LLM agents?", r"AI agents?",
        r"memory architecture", r"memory system", r"conversational agent",
        r"digital human", r"persona", r"\bSLM\b",
    ],
    "ai_music_generation": [
        r"music", r"audio generation", r"musicgen", r"melody", r"instrumental",
        r"score following", r"\bsong\b", r"\bsinging\b", r"text-to-audio",
        r"speech synthesis", r"tts\b",
    ],
    "ai_finance_econometrics": [
        r"finance", r"econometrics", r"arbitrage", r"\btrading\b", r"portfolio",
        r"market", r"\bstock\b", r"option pricing", r"credit risk", r"macroeconomic",
        r"forecast", r"time series", r"causal",
    ],
    "lora_peft_text_only": [
        r"LoRA", r"low-rank", r"PEFT", r"adapter", r"parameter-efficient",
        r"efficient fine-tun", r"fine-tun",
    ],
    # User standing rule (2026-09-02): topological/architectural changes to
    # reasoning language models — looping, recurrent depth, alternative
    # attention. These are KEEP-on-match lanes (see STYLE_GUIDE.md).
    "reasoning_model_topology": [
        r"looped transformer", r"looped language model", r"recurrent depth",
        r"depth.recurren", r"weight.tying", r"weight.tied", r"layer sharing",
        r"shared layer", r"adaptive computation", r"adaptive depth",
        r"early exit", r"linear attention", r"fast weight",
        r"state.space model", r"\bSSM\b", r"\bMamba\b", r"attention variant",
        r"latent reasoning", r"continuous chain.of.thought", r"recurrent memory",
        r"universal transformer", r"iterative refinement of hidden",
    ],
}

# Hard veto: if ANY of these appear, the paper is out (image/video/media).
IMAGE_VIDEO_VETO = [
    r"image generation", r"text-to-image", r"diffusion", r"video generation",
    r"text-to-video", r"image diffusion", r"GAN", r"image-to", r"3d generation",
    r"inpainting", r"outpainting", r"super.?resolution", r"object detection",
    r"segmentation", r"vision foundation model", r"multimodal vision",
    r"image editing", r"\bface\b", r"\bfacial\b", r"photo", r"camera", r"render",
    r"3d reconstruction", r"point cloud", r"lidar", r"depth estimation",
]

# LoRA/PEFT on image/video is explicitly excluded by the user, so a paper that is
# BOTH lora_peft AND image/video gets vetoed (harder than base veto — it's the
# same image_or_video veto, so no separate rule needed; keep for clarity).
LORA_PEFT_KEYWORD = re.compile(r"LoRA|low-rank|PEFT|adapter|parameter-efficient",
                               re.I)


def score_paper(p) -> tuple[list[str], str | None]:
    """Return (matched_flavors, veto_reason_or_None). Matches on paste of
    all text fields so cross-field keyword hits (e.g. keyword in abstract) count."""
    blob = " ".join([
        str(p.get("title") or ""),
        str(p.get("hf_title") or ""),
        str(p.get("summary") or ""),
    ])
    b = blob.lower()

    veto = None
    for frag in IMAGE_VIDEO_VETO:
        if re.search(frag, b):
            veto = f"IMAGE_VIDEO veto ({frag!r})"
            break

    # LoRA/PEFT + image/video is doubly excluded, but image/video veto already
    # covers it. Record whether it was a LoRA paper for the reason output.
    is_lora = LORA_PEFT_KEYWORD.search(b) is not None
    if veto and is_lora:
        veto += " [lora_peft_image_video was also excluded]"

    if veto:
        return [], veto

    matched = [fl for fl, frags in FLAVORS.items()
               if any(re.search(f.lower(), b, re.I) for f in frags)
               or any(re.search(f, b) for f in frags)]
    # de-dup: a paper matching only 'fine-tun' generically should NOT be tagged
    # lora_peft unless it's actually a PEFT/LoRA paper.
    if "lora_peft_text_only" in matched and not is_lora:
        matched.remove("lora_peft_text_only")
    return matched, None


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--cache", required=True, help="feed cache dir")
    ap.add_argument("--config", default=None, help="config.yaml path")
    ap.add_argument("--json-out", default=None, help="write shortlist JSON here")
    args = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_path = args.config or os.path.join(root, "config.yaml")
    cfg = load_config(cfg_path)

    feed_path = os.path.join(args.cache, f"papers-{args.date}.json")
    if not os.path.exists(feed_path):
        # Try exact day; else error with instruction to fetch first.
        print(f"!! no cache {feed_path}", file=sys.stderr)
        print("   run fetch_papers.py --date ... --cache ... first", file=sys.stderr)
        return 2
    with open(feed_path) as f:
        feed = json.load(f)

    include = set(cfg.get("TOPIC_INCLUDE_FLAVORS", []))
    shortlist = []
    for p in feed["papers"]:
        matched, veto = score_paper(p)
        if veto:
            p["_status"] = "vetoed"
            p["_reasons"] = [veto]
            continue
        # Keep if it matches ANY included flavor. If a paper matches no flavor
        # at all, it's not in scope.
        if not matched:
            p["_status"] = "dropped"
            p["_reasons"] = ["no matching included flavor"]
            continue
        kept_flavors = [fl for fl in matched if fl in include]
        if not kept_flavors:
            p["_status"] = "dropped"
            p["_reasons"] = [f"matched only {matched} (not in include set)"]
            continue
        p["_status"] = "keep"
        p["_reasons"] = kept_flavors
        p["_flavor_count"] = len(kept_flavors)
        shortlist.append(p)

    # Rank: more matched flavors first, then fewer comments? Keep stable by
    # flavor count descending, preserving feed order.
    shortlist.sort(key=lambda x: -x.get("_flavor_count", 0))

    print(f"# {feed['papers_date']}: {len(feed['papers'])} total, "
          f"{len([p for p in feed['papers'] if p.get('_status')=='keep'])} kept",
          file=sys.stderr)
    for p in shortlist:
        print(f"  KEEP  [{p['_flavor_count']}] {p['title'][:80]}", file=sys.stderr)
        print(f"        reasons={p['_reasons']}", file=sys.stderr)
    for p in feed["papers"]:
        if p.get("_status") == "vetoed":
            print(f"  VETO  {p['_reasons'][0]}  {p['title'][:70]}", file=sys.stderr)

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(shortlist, f, indent=2, ensure_ascii=False)
    else:
        print(json.dumps(shortlist, indent=2, ensure_ascii=False))

    # Visibility: print silently-dropped papers too, so out-of-scope calls
    # are auditable in the log instead of vanishing without a trace.
    n_dropped = 0
    for p in feed["papers"]:
        if p.get("_status") == "dropped":
            print(f"  DROP  {p['_reasons'][0]}  {p['title'][:70]}", file=sys.stderr)
            n_dropped += 1
    n_veto = sum(1 for p in feed["papers"] if p.get("_status") == "vetoed")
    print(
        f"# kept={len(shortlist)} vetoed={n_veto} dropped={n_dropped} "
        f"total={len(feed['papers'])}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())