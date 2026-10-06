"""
judge.py - STAGE 4 of the tool: decide, for each requirement, whether the deck
addresses it: Covered / Partially covered / Not covered.

Principle (same as Day 3): "AI proposes, Python verifies."
  1. Gemini reads ONE requirement plus the slides (most relevant first, visible
     text only) and returns a verdict, the slide numbers, an exact evidence
     quote, what is missing, a short reason and a confidence level.
  2. Python checks the verdict:
       - the status must be one of the three allowed values
       - the slide numbers must exist and must be among the slides shown
       - the evidence quote must really appear on the cited slides
     Anything that fails a check is flagged "needs review" (never silently fixed).
"""
import csv
import json
import re
from pathlib import Path

from src import llm
from src.extract import quote_found

STATUSES = ["Covered", "Partially covered", "Not covered"]

SYSTEM = (
    "You are a meticulous bid reviewer at a management consultancy. Before a proposal is "
    "submitted, you check whether the deck genuinely addresses each client requirement. "
    "You only give credit for what the slides actually commit to."
)

INSTRUCTIONS = """Decide whether the proposal deck addresses the client requirement below.

STATUS (choose exactly one):
- "Covered": the slides commit to ALL parts of the requirement. Different wording is fine.
- "Partially covered": the slides commit to SOME parts, but at least one part is missing.
- "Not covered": no slide commits to this requirement.

RULES:
1. Judge meaning, not shared words. A slide that merely mentions similar words without committing to this
   requirement for this client does not count (e.g. general claims about the firm, work done for other
   clients, or commercial terms).
2. Check EVERY part of the requirement (e.g. a number or quantity, a second element joined by "and",
   a format or language, a cost element, a deadline). If any part is missing, it is at most "Partially covered".
3. Do not infer anything the slides do not explicitly state.
4. "slides": numbers of the slides that address the requirement (fully or partly); [] if Not covered.
5. "evidence": copy the exact words from the most relevant slide (at most about 30 words); "" if Not covered.
6. "missing": what is not addressed; "" if Covered.

Return JSON only:
{"status": "...", "slides": [0], "evidence": "...", "missing": "...", "reasoning": "one or two sentences", "confidence": "High|Medium|Low"}
"""


def build_prompt(requirement, slides_by_number, ranked):
    parts = [INSTRUCTIONS,
             f"REQUIREMENT ({requirement['category']}): {requirement['requirement']}",
             f'Exact RFP wording: "{requirement["source_quote"]}"',
             "",
             "PROPOSAL SLIDES (visible text only, most relevant first):"]
    for r in ranked:
        slide = slides_by_number[r["slide_number"]]
        parts.append(f"=== Slide {slide['slide_number']} ===\n{slide['visible_text']}")
    return "\n".join(parts)


def _status(value):
    v = str(value).strip().lower()
    if v.startswith("partial"):
        return "Partially covered"
    if v.startswith("not") or v in ("missing", "uncovered", "no"):
        return "Not covered"
    if v.startswith("covered") or v in ("fully covered", "yes"):
        return "Covered"
    return None


def _slide_numbers(value):
    items = value if isinstance(value, list) else [value]
    numbers = []
    for item in items:
        for n in re.findall(r"\d+", str(item)):
            if int(n) not in numbers:
                numbers.append(int(n))
    return numbers


def judge_requirement(requirement, deck, retriever, cache_tag="judge-v1"):
    """Judge one requirement. Returns a verified result record."""
    slides_by_number = {s["slide_number"]: s for s in deck["slides"]}
    ranked = retriever.rank(requirement)
    shown = [r["slide_number"] for r in ranked]

    reply = llm.ask_json(build_prompt(requirement, slides_by_number, ranked),
                         system=SYSTEM, temperature=0.0, cache_tag=cache_tag)
    reply = reply if isinstance(reply, dict) else {}

    flags = []
    status = _status(reply.get("status"))
    if status is None:
        flags.append(f"unclear status '{reply.get('status')}'")
        status = "Needs review"

    cited = _slide_numbers(reply.get("slides", []))
    unknown = [n for n in cited if n not in shown]
    if unknown:
        flags.append(f"cited slides not shown to the judge: {unknown}")
    cited = [n for n in cited if n in shown]

    evidence = str(reply.get("evidence") or "").strip()
    if status == "Not covered":
        cited, evidence_check = [], "n/a"
    elif not cited:
        evidence_check = "no slides cited"
        flags.append("verdict gives credit but cites no valid slide")
    elif evidence and any(quote_found(evidence, slides_by_number[n]["visible_text"], threshold=0.85) for n in cited):
        evidence_check = "verified"
    else:
        evidence_check = "NOT FOUND on cited slides"
        flags.append("evidence quote not found on the cited slides")

    return {
        "id": requirement["id"],
        "category": requirement["category"],
        "requirement": requirement["requirement"],
        "rfp_section": requirement["section"],
        "rfp_quote": requirement["source_quote"],
        "status": status,
        "slides": cited,
        "evidence": evidence,
        "evidence_check": evidence_check,
        "missing": str(reply.get("missing") or "").strip(),
        "reasoning": str(reply.get("reasoning") or "").strip(),
        "confidence": str(reply.get("confidence") or "").strip().capitalize() or "Unknown",
        "needs_review": bool(flags),
        "review_reasons": "; ".join(flags),
        "top_retrieved": [r["slide_number"] for r in ranked[:3]],
        "model": llm.last_model_used,
    }


def judge_all(requirements, deck, retriever, progress=print, cache_tag="judge-v1"):
    """Judge every requirement, one Gemini call each (cached, so reruns are free)."""
    results = []
    for i, req in enumerate(requirements, start=1):
        result = judge_requirement(req, deck, retriever, cache_tag=cache_tag)
        results.append(result)
        slides = ", ".join(map(str, result["slides"])) or "-"
        flag = "  ⚠️ review" if result["needs_review"] else ""
        progress(f"[{i}/{len(requirements)}] {result['id']} {result['status']:<18} slides: {slides:<8}{flag}")
    return results


def save_judgements(results, folder="output"):
    """Save all verdicts as JSON (full detail) and CSV (one row per requirement)."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "judgements.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    fields = ["id", "category", "requirement", "status", "slides", "evidence", "evidence_check", "missing",
              "reasoning", "confidence", "needs_review", "review_reasons", "rfp_section", "rfp_quote", "model"]
    with open(folder / "judgements.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow({**r, "slides": ", ".join(map(str, r["slides"]))})
    return folder / "judgements.json", folder / "judgements.csv"
