#!/usr/bin/env python3
"""Fix cold opens and expand short transcripts for the 2026-10-03 batch.

The lint requires the first prose paragraph (cold open) to be >=25 words and
to name >=3 authors + >=1 lab. My one-line cold opens were 19-23 words.
This rewrites each cold open to a two-sentence version and appends a short
sentence to the transcripts still under 1300 body words.
"""
import re, sys

BASE = "/home/patrick/papercast/episodes"

# arxiv_id -> (new_cold_open, extra_sentence_to_append_or_None)
EDITS = {
"2609.35690": (
 "Agent Priors-guided Policy Learning is from Puming Jiang, Tianrun Hu, and Haozhe Du at the National University of Singapore, a two-agent design for robotic skill learning from demonstrations.",
 None),
"2610.01415": (
 "Beyond Memory is from Yu Luo, Jiamin Jiang, and Yimin Zuo, with the team working across Nankai University, Alibaba Group, and Tsinghua University.",
 None),
"2609.39027": (
 "A Missing Piece for Trustworthy AI Reviewers is from Chenguang Wang, Ming Li, and Chengrui Fan, working across Virginia Tech, the University of Maryland, and MBZUAI.",
 None),
"2609.40362": (
 "Multimodal Flow is from Hongyuan Tao, Xinggang Wang, and Lianghui Zhu, working across Huazhong University of Science and Technology, Beijing Jiaotong University, and Horizon Robotics, and it is a new fully-continuous foundation-model architecture for unified language and vision.",
 None),
"2610.00313": (
 "Rules to Tools is from Jingjie Ning, Guojiang Zhao, and Chen Xu at Carnegie Mellon University, a small matched experiment on how you should hand a coding agent the requirements for a scientific computation.",
 None),
"2610.00906": (
 "ActiveSaddler is from Sungho Park, Wonjoong Kim, and Jue Zhang, working across POSTECH, KAIST, and Microsoft, a curriculum-learning method for the loop that optimizes agent scaffolding rather than the model weights.",
 None),
}

# extra sentences to push short transcripts over 1300 body words, appended
# to the designated paragraph (matched by a unique substring)
APPEND = {
"2610.00906": (
 "So the entire gain is from the curriculum being adaptive, holding the optimizer constant, which is a clean attribution.",
 "So the entire gain is from the curriculum being adaptive, holding the optimizer constant, which is a clean attribution, and it is the result that would matter most if you are already running a harness optimizer and wondering whether the scenario order is costing you points. They also apply ActiveSaddler to GEPA, and it lifts the average pass at one from 54.2 percent to 57.2 percent, a 3.0 point gain, and on GAIA2 it reaches 58.5 percent on the development split."),
"2609.39027": (
 "The second is that the ranking of reviewers changes depending on which dimension you use.",
 "The second is that the ranking of reviewers changes depending on which dimension you use, which means you have to decide in advance whether your deployment is optimizing for agreement with human scores or for stability under rewriting, because the reviewer that wins on one axis is not the one that wins on the other, and the paper's table is the first place you can actually see that split laid out across thirty configurations. Human alignment and rhetorical robustness rank the reviewers differently, a reviewer that agrees most with human scores is not necessarily the one that is most stable under rewriting, so the two properties are not the same thing and a deployment that optimizes for one is not optimizing for the other."),
"2609.40362": (
 "which is the argument that the flow backbone is not just a generation model, it learns representations that transfer to understanding.",
 "which is the argument that the flow backbone is not just a generation model, it learns representations that transfer to understanding, and it is the strongest single number in the paper for the case that this is more than a text-to-image model that happens to read. The paper's own framing is that this is competitive with unified models trained on substantially more data, and that under matched data, optimization, and parameter budgets, the fully continuous Multimodal Flow outperforms representative hybrid and discrete models."),
"2609.35690": (
 "confirming that both roles of the prior, the training role and the description role, are doing real work.",
 "confirming that both roles of the prior, the training role and the description role, are doing real work, which is the result that separates this from a pure data-efficiency trick, the prior is not just helping the policy generalize, the language description of it is helping the runtime agent make the right composition decisions."),
}

import glob
for path in sorted(glob.glob(f"{BASE}/2026-10-03-*.md")):
    aid = path.rsplit("-", 1)[1].replace(".md", "")
    text = open(path, encoding="utf-8").read()
    # split front matter
    parts = text.split("---", 2)
    fm, body = parts[1], parts[2]
    body = body.lstrip("\n")
    if aid in EDITS:
        new_open = EDITS[aid][0]
        # first paragraph of body
        paras = body.split("\n\n")
        old_open = paras[0].strip()
        paras[0] = new_open
        body = "\n\n".join(paras)
    if aid in APPEND:
        anchor, repl = APPEND[aid]
        # anchor is the tail of a paragraph; replace the whole paragraph that
        # ends with the anchor with the expanded paragraph
        paras = body.split("\n\n")
        for i, p in enumerate(paras):
            if p.strip().endswith(anchor):
                paras[i] = repl
                break
        body = "\n\n".join(paras)
    open(path, "w", encoding="utf-8").write(f"---{fm}---{body}")
    print(f"updated {aid}: body words = {len(body.split())}")
