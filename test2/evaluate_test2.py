"""
evaluate_test2.py - scores the tool on Test 2 (the unseen scenario).

    python -m test2.evaluate_test2

Same metrics, same order and same keyword baseline (thresholds 0.50 / 0.25, fixed before
Test 1 ever ran) as the official evaluation. Reads only test_data_2/ and output_test2/.

Matching planted -> extracted requirements: the Test 2 RFP REWORDS every requirement, so
matching uses the exact RFP sentence Gemini reported for each planted requirement
("planted_quote") against each extracted requirement's RFP quote (shared content words,
overlap coefficient >= 0.6). Every match is printed so a person can check it.
"""
import json
from pathlib import Path

from evaluation.check_extraction import content_words
from evaluation.keyword_baseline import COVERED_AT, PARTIAL_AT, keyword_verdicts
from src.parsers import parse_deck
from test2.scenario2 import TRAPS

KEY = Path("test_data_2/ground_truth/answer_key.json")
OUT = Path("output_test2")
DECK = "test_data_2/inputs/proposal_test2.pptx"
STATUSES = ["Covered", "Partially covered", "Not covered"]


def _overlap(a, b):
    wa, wb = content_words(a), content_words(b)
    return len(wa & wb) / min(len(wa), len(wb)) if wa and wb else 0.0


def match_requirements(planted, extracted, threshold=0.6):
    """For each planted requirement, the extracted one whose RFP quote overlaps its planted quote most."""
    links = []
    for gt in planted:
        scored = sorted(((_overlap(gt["planted_quote"], r["source_quote"]),
                          _overlap(gt["text"], r["requirement"] + " " + r["source_quote"]), r) for r in extracted),
                        key=lambda x: (-x[0], -x[1]))
        best = scored[0] if scored else (0.0, 0.0, None)
        found = best[2] is not None and best[0] >= threshold
        links.append({"planted_id": gt["id"], "req_id": best[2]["id"] if found else "", "score": round(best[0], 2),
                      "category_ok": found and best[2]["category"] == gt["category"]})
    return links


def score(verdicts, planted, links):
    by_id = {v["id"]: v for v in verdicts}
    rows = []
    for gt, link in zip(planted, links):
        v = by_id.get(link["req_id"])
        predicted = v["status"] if v else "Not extracted"
        slides = v["slides"] if v else []
        slide_ok = (not slides) if gt["expected_status"] == "Not covered" else bool(set(gt["expected_slides"]) & set(slides))
        rows.append({"planted_id": gt["id"], "req_id": link["req_id"], "expected": gt["expected_status"],
                     "predicted": predicted, "status_ok": predicted == gt["expected_status"],
                     "expected_slides": gt["expected_slides"], "predicted_slides": slides, "slide_ok": slide_ok})
    gaps = [r for r in rows if r["expected"] != "Covered"]
    covered = [r for r in rows if r["expected"] == "Covered"]
    return {
        "rows": rows,
        "gaps_caught": f"{sum(r['predicted'] != 'Covered' for r in gaps)}/{len(gaps)}",
        "status_accuracy": f"{sum(r['status_ok'] for r in rows)}/{len(rows)}",
        "false_alarms": f"{sum(r['predicted'] != 'Covered' for r in covered)}/{len(covered)}",
        "slide_accuracy": f"{sum(r['slide_ok'] for r in rows)}/{len(rows)}",
        "traps_fooled": f"{sum(TRAPS[r['planted_id']] in r['predicted_slides'] for r in rows if r['planted_id'] in TRAPS)}/{len(TRAPS)}",
        "confusion": {e: {p: sum(r["expected"] == e and r["predicted"] == p for r in rows) for p in STATUSES} for e in STATUSES},
    }


def best_baseline(requirements, deck, planted, links):
    best = None
    for c in [x / 100 for x in range(20, 95, 5)]:
        for p in [x / 100 for x in range(5, 90, 5)]:
            if p >= c:
                continue
            sc = score(keyword_verdicts(requirements, deck, c, p), planted, links)
            key = (int(sc["status_accuracy"].split("/")[0]), int(sc["gaps_caught"].split("/")[0]),
                   -int(sc["false_alarms"].split("/")[0]))
            if best is None or key > best[0]:
                best = (key, c, p, sc)
    return best[1], best[2], best[3]


def main():
    planted = json.loads(KEY.read_text(encoding="utf-8"))
    extraction = json.loads((OUT / "requirements.json").read_text(encoding="utf-8"))
    verdicts = json.loads((OUT / "judgements.json").read_text(encoding="utf-8"))
    requirements = extraction["requirements"]
    deck = parse_deck(DECK)

    links = match_requirements(planted, requirements)
    found = sum(bool(l["req_id"]) for l in links)
    matched_ids = {l["req_id"] for l in links if l["req_id"]}
    extras = [r for r in requirements if r["id"] not in matched_ids]
    tool = score(verdicts, planted, links)
    base = score(keyword_verdicts(requirements, deck), planted, links)
    c, p, base_best = best_baseline(requirements, deck, planted, links)
    models = sorted({str(v["model"]).replace("cache: ", "") for v in verdicts})
    gen = json.loads(Path("test_data_2/ground_truth/generation_info.json").read_text(encoding="utf-8"))["generator_models"]
    run = json.loads((OUT / "run_info.json").read_text(encoding="utf-8"))
    tool_models = sorted({run["extraction_model"], run["judge_model"]})
    separated = not (set(gen) & set(tool_models))

    result = {"extraction": {"found": f"{found}/{len(planted)}", "requirements_listed": len(requirements),
                             "category_agreement": f"{sum(l['category_ok'] for l in links)}/{found}",
                             "extras": [(e["id"], e["requirement"]) for e in extras], "links": links,
                             "model": extraction.get("model")},
              "judge_models": models, "generator_models": gen, "tool_models": tool_models,
              "models_separated": separated, "tool": tool,
              "baseline": {**{k: v for k, v in base.items() if k != "rows"}, "thresholds": [COVERED_AT, PARTIAL_AT]},
              "baseline_best": {**{k: v for k, v in base_best.items() if k != "rows"}, "thresholds": [c, p]}}
    (OUT / "test2_report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    t, b, bb = tool, result["baseline"], result["baseline_best"]
    lines = ["# Test 2: unseen scenario (healthcare), live run", "",
             f"Extraction: {found}/{len(planted)} planted requirements found; {len(requirements)} listed; "
             f"{len(extras)} extras.", "",
             f"Documents written by: {', '.join(gen)} · tool (extraction + judge) run by: {', '.join(tool_models)} · "
             f"different models: {'yes' if separated else 'NO (limitation)'}", "",
             f"| Metric | The tool | Keyword baseline ({COVERED_AT}/{PARTIAL_AT}, fixed) | Keyword baseline, best possible ({c}/{p}, tuned) |",
             "|---|---|---|---|"]
    for key, label in [("gaps_caught", "**1. Gaps caught (primary)**"), ("status_accuracy", "2. Status accuracy"),
                       ("false_alarms", "3. False alarms (lower is better)"), ("slide_accuracy", "4. Slide accuracy"),
                       ("traps_fooled", "Keyword traps fooled (lower is better)")]:
        lines.append(f"| {label} | {t[key]} | {b[key]} | {bb[key]} |")
    lines += ["", "| Planted | Matched | Expected | Tool | Expected slides | Tool slides |", "|---|---|---|---|---|---|"]
    for r, l in zip(t["rows"], links):
        lines.append(f"| {r['planted_id']} | {r['req_id'] or '-'} ({l['score']}) | {r['expected']} | "
                     f"{'✅' if r['status_ok'] else '❌'} {r['predicted']} | {r['expected_slides']} | {r['predicted_slides']} |")
    (OUT / "test2_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return result


if __name__ == "__main__":
    main()
