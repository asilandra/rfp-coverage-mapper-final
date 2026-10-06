"""
check_coverage.py - EVALUATION of stages 3-4 (retrieval and judge).

NOT part of the tool: the "exam marking" step, allowed to read ground_truth/.
Scored ONLY on the 18 planted requirements (decision 39: the answer key was
fixed before the documents existed). Extra requirements are reported, not scored.

Measures:
  - status accuracy: judge's verdict == planted status (Covered / Partial / Not covered)
  - gap detection: of the 8 planted gaps (4 partial + 4 missing), how many the
    tool flags as NOT fully covered; and false alarms among the 10 covered ones
  - slide accuracy: for covered/partial, did the judge cite a correct slide?
                    for not covered, did it cite no slide?
  - retrieval rank: position of the correct slide in the embedding ranking
"""
import json
from pathlib import Path

from evaluation.check_extraction import evaluate_extraction

STATUSES = ["Covered", "Partially covered", "Not covered"]


def evaluate_coverage(judgements, extraction_result, answer_key_path="test_data/ground_truth/answer_key.json"):
    planted = {g["id"]: g for g in json.loads(Path(answer_key_path).read_text(encoding="utf-8"))}
    links = evaluate_extraction(extraction_result, answer_key_path)   # planted ID -> extracted R-ID
    by_id = {j["id"]: j for j in judgements}

    rows = []
    for link in links["rows"]:
        gt = planted[link["planted_id"]]
        j = by_id.get(link["match_id"])
        predicted = j["status"] if j else "Not extracted"
        pred_slides = j["slides"] if j else []
        if gt["expected_status"] == "Not covered":
            slide_ok = not pred_slides
        else:
            slide_ok = bool(set(gt["expected_slides"]) & set(pred_slides))
        rows.append({
            "planted_id": gt["id"], "req_id": link["match_id"], "requirement": gt["text"],
            "expected": gt["expected_status"], "predicted": predicted,
            "status_ok": predicted == gt["expected_status"],
            "expected_slides": gt["expected_slides"], "predicted_slides": pred_slides,
            "slide_ok": slide_ok,
        })

    gaps = [r for r in rows if r["expected"] != "Covered"]
    covered = [r for r in rows if r["expected"] == "Covered"]
    confusion = {e: {p: sum(r["expected"] == e and r["predicted"] == p for r in rows) for p in STATUSES}
                 for e in STATUSES}
    scored_ids = {r["req_id"] for r in rows}
    return {
        "rows": rows,
        "total": len(rows),
        "status_correct": sum(r["status_ok"] for r in rows),
        "gaps_total": len(gaps),
        "gaps_caught": sum(r["predicted"] != "Covered" for r in gaps),
        "covered_total": len(covered),
        "false_alarms": sum(r["predicted"] != "Covered" for r in covered),
        "slide_correct": sum(r["slide_ok"] for r in rows),
        "confusion": confusion,
        "extras": [j for j in judgements if j["id"] not in scored_ids],
    }


def retrieval_ranks(retriever, requirements, extraction_result, answer_key_path="test_data/ground_truth/answer_key.json"):
    """For each planted requirement that has a correct slide: where does it rank? (1 = top)"""
    planted = {g["id"]: g for g in json.loads(Path(answer_key_path).read_text(encoding="utf-8"))}
    links = evaluate_extraction(extraction_result, answer_key_path)
    req_by_id = {r["id"]: r for r in requirements}
    ranks = {}
    for link in links["rows"]:
        gt = planted[link["planted_id"]]
        if not gt["expected_slides"] or link["match_id"] not in req_by_id:
            continue
        order = [r["slide_number"] for r in retriever.rank(req_by_id[link["match_id"]], limit=10**6)]
        ranks[gt["id"]] = min(order.index(n) + 1 for n in gt["expected_slides"] if n in order)
    return ranks
