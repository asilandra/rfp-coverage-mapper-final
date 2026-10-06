"""
generate_test2.py - builds the Test 2 documents from scenario2.py (answer key first).

    python -m test2.generate_test2

Writes ONLY to test_data_2/ (never to the official test_data/).
Reuses the official file builders unchanged; only the prompts are new.
Run with LLM_CACHE_DIR=cache_test2 so Test 2's Gemini answers never mix with the official cache,
and with GEMINI_MODEL set to the GENERATOR model and no fallback, so the documents are written by a
different model from the one that runs the tool. The model actually used is recorded.
"""
import json
from pathlib import Path

from src.extract import quote_found
from src import llm
from src.llm import ask_json
from src.parsers import parse_rfp
from synthetic.generate_test_data import build_deck, build_rfp_docx, build_rfp_pdf
from test2.scenario2 import CLIENT, CONSULTANT, PROJECT, REQUIREMENTS, SLIDES, expected_answer_key

INPUTS = Path("test_data_2/inputs")
TRUTH = Path("test_data_2/ground_truth")

RFP_PROMPT = f"""
You are the head of procurement at {CLIENT}, a fictional healthcare group (4 hospitals and 12 outpatient clinics).
Write a realistic, detailed Request for Proposal (RFP) for "{PROJECT}".

It MUST contain every requirement below. Rules:
- REWORD each requirement in your own procurement language. Do not copy the wording below; vary the
  phrasing ("The Supplier will...", "Bidders are required to...", "It is expected that...", "...must be provided").
- Keep the meaning, numbers and every part of each requirement (e.g. both services, all sites, both languages).
- Do NOT show the IDs (S1, D2...) in the document.
- Use numbered sections with sub-sections (e.g. "3. Scope of Services" then "3.1 Patient Insight").
  Put some requirements in bullets and weave others into longer paragraphs.
- Also include sections that are NOT requirements: background, objectives, evaluation criteria with
  weights, submission instructions (deadline 15 November 2026), commercial and legal terms.
- Do not add extra requirements beyond the list. Roughly 1,500-2,000 words.

Requirements:
{json.dumps([{"id": r["id"], "text": r["text"]} for r in REQUIREMENTS], indent=1)}

Return JSON:
{{
  "title": "...",
  "reference": "RFP reference number",
  "sections": [{{"heading": "1. ...", "paragraphs": ["..."], "bullets": ["..."]}}],
  "requirement_quotes": {{"S1": "the EXACT sentence or bullet from your RFP text that states this requirement", "...": "..."}}
}}
Each requirement_quotes value must be copied character for character from your own text above.
"""


def deck_prompt():
    plan = [{"slide_number": s["n"], "working_title": s["title"], "brief": s["brief"],
             "forbidden_words": s.get("avoid", []), "needs_table": s.get("table", False)} for s in SLIDES]
    return f"""
You are a consultant at {CONSULTANT} (a fictional firm) writing a proposal deck for {CLIENT} on "{PROJECT}".
Write the text for EXACTLY {len(SLIDES)} slides, following each brief closely.
Rules:
- Confident consulting language in your OWN words.
- Never use a slide's forbidden_words (or close variants) on that slide.
- Never cover something a brief does not ask for.
- 3-5 bullets per slide, each under 25 words. Short speaker notes per slide.
- If needs_table is true, put the content in "table" and keep bullets short.

Slide plan:
{json.dumps(plan, indent=1)}

Return JSON:
{{"slides": [{{"slide_number": 1, "title": "...", "bullets": ["..."], "notes": "...",
              "table": {{"headers": ["..."], "rows": [["..."]]}} or null}}]}}
"""


def check_rfp(pdf_path, rfp):
    """Every requirement must have a quote that really appears in the built PDF."""
    text = parse_rfp(pdf_path)["full_text"]
    quotes = rfp.get("requirement_quotes") or {}
    return [r["id"] for r in REQUIREMENTS if not (quotes.get(r["id"]) and quote_found(quotes[r["id"]], text))]


def check_deck(slides):
    problems = []
    if len(slides) != len(SLIDES):
        problems.append(f"Expected {len(SLIDES)} slides, got {len(slides)}")
    for plan, slide in zip(SLIDES, slides):
        text = json.dumps(slide).lower()
        problems += [f"Slide {plan['n']} uses forbidden word '{w}'" for w in plan.get("avoid", []) if w.lower() in text]
    return problems


def main():
    INPUTS.mkdir(parents=True, exist_ok=True)
    TRUTH.mkdir(parents=True, exist_ok=True)
    used = set()

    print("Step 1/3: Gemini writes the Test 2 RFP...")
    for attempt in range(1, 4):
        rfp = ask_json(RFP_PROMPT, temperature=0.7, cache_tag=f"rfp2-attempt-{attempt}")
        used.add(str(llm.last_model_used).replace("cache: ", ""))
        build_rfp_docx(rfp, INPUTS / "rfp_test2.docx")
        build_rfp_pdf(rfp, INPUTS / "rfp_test2.pdf")
        missing = check_rfp(INPUTS / "rfp_test2.pdf", rfp)
        print(f"  attempt {attempt}: requirement quotes not found in the PDF: {missing or 'none'}")
        if not missing:
            break
    if missing:
        raise SystemExit(f"RFP check failed after 3 attempts (missing: {missing})")

    print("Step 2/3: Gemini writes the Test 2 deck...")
    best, best_problems = None, None
    for attempt in range(1, 4):
        reply = ask_json(deck_prompt(), temperature=0.7, cache_tag=f"deck2-attempt-{attempt}")
        used.add(str(llm.last_model_used).replace("cache: ", ""))
        slides = reply.get("slides") if isinstance(reply, dict) else []
        slides = slides if isinstance(slides, list) else []
        problems = check_deck(slides)
        print(f"  attempt {attempt}: {len(problems)} rule violation(s)")
        if best is None or len(problems) < len(best_problems):
            best, best_problems = slides, problems
        if not problems:
            break
    build_deck(best, INPUTS / "proposal_test2.pptx")
    for p in best_problems:
        print("  WARNING:", p)

    print("Step 3/3: saving the answer key...")
    key = expected_answer_key()
    for row in key:
        row["planted_quote"] = rfp["requirement_quotes"][row["id"]]
    (TRUTH / "answer_key.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    (TRUTH / "rfp_content.json").write_text(json.dumps(rfp, indent=2), encoding="utf-8")
    (TRUTH / "deck_content.json").write_text(json.dumps(best, indent=2), encoding="utf-8")
    (TRUTH / "generation_info.json").write_text(json.dumps({"generator_models": sorted(used)}, indent=2), encoding="utf-8")
    print(f"Documents written by: {sorted(used)}")
    counts = {s: sum(r["expected_status"] == s for r in key) for s in ("Covered", "Partially covered", "Not covered")}
    print(f"Done. Answer key: {counts} | deck rule violations: {len(best_problems)}")


if __name__ == "__main__":
    main()
