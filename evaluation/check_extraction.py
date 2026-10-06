"""
check_extraction.py - EVALUATION of stage 2 (requirement extraction).

This is NOT part of the tool. It is the "exam marking" step and the only kind
of code allowed to read the answer key in test_data/ground_truth/.

Question it answers: of the 18 requirements we planted in the RFP,
how many did the tool find (recall), and what else did it list?

Matching method (simple and transparent): for each planted requirement, find
the extracted requirement that shares the most content words with it.
score = shared content words / content words in the planted requirement.
A score of 0.5 or more counts as "found". Every match is printed, so a human
can check the matching itself.
"""
import json
import re
from pathlib import Path

STOPWORDS = set("""a an the and or of to for in on at by with from as is are be been all each
its it this that these those any into than then their our your shall must will should can
including include includes both least within over per""".split())


def content_words(text):
    """Meaningful words only (numbers are kept, e.g. '16', '500')."""
    return {w for w in re.findall(r"[a-z0-9]+", str(text).lower())
            if w.isdigit() or (len(w) > 2 and w not in STOPWORDS)}


def overlap(planted_text, extracted):
    planted = content_words(planted_text)
    found = content_words(extracted["source_quote"] + " " + extracted["requirement"])
    return len(planted & found) / len(planted) if planted else 0.0


def evaluate_extraction(result, answer_key_path="test_data/ground_truth/answer_key.json", threshold=0.5):
    planted = json.loads(Path(answer_key_path).read_text(encoding="utf-8"))
    extracted = result["requirements"]
    rows, used = [], {}
    for gt in planted:
        scored = sorted(((overlap(gt["text"], r), r) for r in extracted), key=lambda x: -x[0])
        score, best = scored[0] if scored else (0.0, None)
        hit = best is not None and score >= threshold
        if hit:
            used.setdefault(best["id"], []).append(gt["id"])
        rows.append({"planted_id": gt["id"], "category": gt["category"], "planted": gt["text"],
                     "found": hit, "match_id": best["id"] if hit else "", "score": round(score, 2),
                     "category_ok": hit and best["category"] == gt["category"]})
    merged = {rid: ids for rid, ids in used.items() if len(ids) > 1}
    extras = [r for r in extracted if r["id"] not in used]
    found = sum(r["found"] for r in rows)
    return {"rows": rows, "found": found, "total": len(planted), "recall": found / len(planted),
            "category_agreement": sum(r["category_ok"] for r in rows) / max(found, 1),
            "merged": merged, "extras": extras}
