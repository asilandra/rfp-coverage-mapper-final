"""
final_evaluation.py - the final scoring (Day 5): the tool vs the keyword baseline.

Scored on the 18 planted requirements only (decision 39).
Reported in the agreed order (decision 52):
  1. gap detection (primary)  2. status accuracy  3. false alarms  4. slide accuracy
Plus: the keyword traps, and the baseline's best possible (threshold-tuned) result.
"""
import json
from pathlib import Path

from evaluation.check_coverage import evaluate_coverage
from evaluation.keyword_baseline import COVERED_AT, PARTIAL_AT, keyword_verdicts

# Planted traps (from the Day 1 scenario design): requirement -> slide that shares its keywords
TRAPS = {"S4": 13, "S6": 2, "T3": 13, "S2": 14, "D3": 14}


def _metrics(ev):
    return {
        "gaps_caught": f"{ev['gaps_caught']}/{ev['gaps_total']}",
        "status_accuracy": f"{ev['status_correct']}/{ev['total']}",
        "false_alarms": f"{ev['false_alarms']}/{ev['covered_total']}",
        "slide_accuracy": f"{ev['slide_correct']}/{ev['total']}",
    }


def trap_results(ev):
    """Did the method cite the trap slide for its requirement? (citing it = fooled)"""
    out = {}
    for row in ev["rows"]:
        if row["planted_id"] in TRAPS:
            out[row["planted_id"]] = TRAPS[row["planted_id"]] in row["predicted_slides"]
    return out


def best_baseline(requirements, deck, extraction):
    """The baseline's best status accuracy over a grid of thresholds (tuned on the answers = optimistic)."""
    best = None
    for c in [x / 100 for x in range(20, 95, 5)]:
        for p in [x / 100 for x in range(5, 90, 5)]:
            if p >= c:
                continue
            ev = evaluate_coverage(keyword_verdicts(requirements, deck, c, p), extraction)
            key = (ev["status_correct"], ev["gaps_caught"], -ev["false_alarms"])
            if best is None or key > best[0]:
                best = (key, c, p, ev)
    return best[1], best[2], best[3]


def compare(tool_verdicts, requirements, deck, extraction, judge_model):
    tool = evaluate_coverage(tool_verdicts, extraction)
    base_verdicts = keyword_verdicts(requirements, deck)
    base = evaluate_coverage(base_verdicts, extraction)
    c, p, base_best = best_baseline(requirements, deck, extraction)
    return {
        "judge_model": judge_model,
        "tool": {**_metrics(tool), "traps_fooled": sum(trap_results(tool).values()), "eval": tool},
        "baseline": {**_metrics(base), "traps_fooled": sum(trap_results(base).values()),
                     "thresholds": [COVERED_AT, PARTIAL_AT], "eval": base, "verdicts": base_verdicts},
        "baseline_best": {**_metrics(base_best), "traps_fooled": sum(trap_results(base_best).values()),
                          "thresholds": [c, p]},
        "traps_total": len(TRAPS),
    }


def write_report(result, path="output/evaluation_report.md"):
    t, b, bb = result["tool"], result["baseline"], result["baseline_best"]
    lines = [
        "# Evaluation report: coverage judging",
        "",
        f"Scored on the 18 planted requirements (answer key written before the documents existed). "
        f"Judge model for all requirements: **{result['judge_model']}**.",
        "",
        "| Metric | The tool | Keyword baseline (pre-registered thresholds "
        f"{b['thresholds'][0]}/{b['thresholds'][1]}) | Keyword baseline, best possible (tuned on the answers: "
        f"{bb['thresholds'][0]}/{bb['thresholds'][1]}) |",
        "|---|---|---|---|",
        f"| **1. Gaps caught (primary)** | **{t['gaps_caught']}** | {b['gaps_caught']} | {bb['gaps_caught']} |",
        f"| 2. Status accuracy | {t['status_accuracy']} | {b['status_accuracy']} | {bb['status_accuracy']} |",
        f"| 3. False alarms (lower is better) | {t['false_alarms']} | {b['false_alarms']} | {bb['false_alarms']} |",
        f"| 4. Slide accuracy | {t['slide_accuracy']} | {b['slide_accuracy']} | {bb['slide_accuracy']} |",
        f"| Keyword traps fooled by (lower is better) | {t['traps_fooled']}/{result['traps_total']} | "
        f"{b['traps_fooled']}/{result['traps_total']} | {bb['traps_fooled']}/{result['traps_total']} |",
        "",
        "**How to read this:** gap detection is the primary metric, but it must be read together with false alarms: "
        "a method that flags everything as a gap also \"catches\" every gap. The baseline's best-possible column "
        "is optimistic on purpose (its thresholds were tuned on the answer key); the tool's prompt was not tuned.",
        "",
        "## Requirement by requirement (planted answer vs tool vs baseline)",
        "",
        "| Planted | Expected | Tool | Baseline | Expected slides | Tool slides | Baseline slides |",
        "|---|---|---|---|---|---|---|",
    ]
    for tr, br in zip(t["eval"]["rows"], b["eval"]["rows"]):
        mark = lambda ok: "✅" if ok else "❌"
        lines.append(f"| {tr['planted_id']} | {tr['expected']} | {mark(tr['status_ok'])} {tr['predicted']} | "
                     f"{mark(br['status_ok'])} {br['predicted']} | {tr['expected_slides']} | "
                     f"{tr['predicted_slides']} | {br['predicted_slides']} |")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    slim = {k: ({kk: vv for kk, vv in v.items() if kk not in ("eval", "verdicts")} if isinstance(v, dict) else v)
            for k, v in result.items()}
    Path(path).with_suffix(".json").write_text(json.dumps(slim, indent=2), encoding="utf-8")
    return path
