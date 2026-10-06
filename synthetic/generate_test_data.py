"""
generate_test_data.py - creates the synthetic test set.

Run from the project root:
    python -m synthetic.generate_test_data

Output folders (kept separate on purpose):
  test_data/inputs/        -> the ONLY files the tool is allowed to read
  test_data/ground_truth/  -> answer key + raw Gemini output, used ONLY by
                              the Day 5 evaluation, never by the tool itself

Steps:
  1. Gemini writes the RFP text (as JSON)    -> we build .docx AND .pdf
  2. Gemini writes the slide text (as JSON)  -> we build .pptx
  3. We check Gemini followed the plan (no forbidden words on slides)
  4. We save the answer key (.json + .csv)

Gemini writes the WORDS; Python builds the FILES. That way the file structure
is always valid, and the answer key never depends on what Gemini decided.
"""
import csv
import json
from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from pptx import Presentation
from pptx.util import Inches, Pt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

from src.llm import ask_json
from synthetic.scenario import CLIENT, CONSULTANT, PROJECT, REQUIREMENTS, SLIDES, expected_answer_key

INPUTS = Path("test_data/inputs")
TRUTH = Path("test_data/ground_truth")

# ---------------------------------------------------------------------------
# Step 1: RFP
# ---------------------------------------------------------------------------
RFP_PROMPT = f"""
You are a procurement officer at {CLIENT}, a fictional logistics group in Dubai.
Write a realistic Request for Proposal (RFP) for "{PROJECT}".

It MUST contain every requirement below. Rules:
- Rephrase each in formal procurement language ("The Consultant shall...").
- Do NOT show the IDs (S1, D2...) in the document.
- Put about half of them as bullet points and weave the rest into paragraphs,
  so they are not all neatly listed.
- Also include normal RFP sections that are NOT consultant requirements:
  background, objectives, evaluation criteria with weights, submission
  instructions (deadline 20 October 2026), confidentiality.
- Do not add extra scope requirements beyond the list.
- Keep the whole RFP to roughly 1,500-2,000 words.

Requirements:
{json.dumps([{"id": r["id"], "text": r["text"]} for r in REQUIREMENTS], indent=1)}

Return JSON:
{{
  "title": "...",
  "reference": "RFP reference number",
  "sections": [{{"heading": "1. ...", "paragraphs": ["..."], "bullets": ["..."]}}],
  "requirement_locations": {{"S1": "heading of the section where it appears", "...": "..."}}
}}
"""


def generate_rfp():
    print("Step 1/4: asking Gemini to write the RFP...")
    rfp = ask_json(RFP_PROMPT, temperature=0.7, cache_tag="rfp")
    missing = [r["id"] for r in REQUIREMENTS if r["id"] not in rfp.get("requirement_locations", {})]
    if missing:
        print(f"  WARNING: Gemini did not confirm placing: {missing}. Check the RFP manually.")
    return rfp


def build_rfp_docx(rfp, path):
    doc = Document()
    doc.add_heading(str(rfp.get("title") or "Request for Proposal"), level=0)
    doc.add_paragraph(f"Reference: {rfp.get('reference') or ''}")
    for sec in rfp.get("sections") or []:
        doc.add_heading(str(sec.get("heading") or ""), level=1)
        for p in sec.get("paragraphs") or []:
            doc.add_paragraph(str(p))
        for b in sec.get("bullets") or []:
            doc.add_paragraph(str(b), style="List Bullet")
    doc.save(path)


def build_rfp_pdf(rfp, path):
    styles = getSampleStyleSheet()
    story = [Paragraph(escape(str(rfp.get("title") or "Request for Proposal")), styles["Title"]),
             Paragraph(escape(f"Reference: {rfp.get('reference') or ''}"), styles["Normal"]),
             Spacer(1, 12)]
    for sec in rfp.get("sections") or []:
        story.append(Paragraph(escape(str(sec.get("heading") or "")), styles["Heading2"]))
        for p in sec.get("paragraphs") or []:
            story.append(Paragraph(escape(str(p)), styles["BodyText"]))
            story.append(Spacer(1, 6))
        bullets = sec.get("bullets") or []
        if bullets:
            story.append(ListFlowable(
                [ListItem(Paragraph(escape(str(b)), styles["BodyText"])) for b in bullets],
                bulletType="bullet"))
    SimpleDocTemplate(str(path), pagesize=A4).build(story)


# ---------------------------------------------------------------------------
# Step 2: Deck
# ---------------------------------------------------------------------------
def deck_prompt():
    plan = [{"slide_number": s["n"], "working_title": s["title"], "brief": s["brief"],
             "forbidden_words": s.get("avoid", []), "needs_table": s.get("table", False)}
            for s in SLIDES]
    return f"""
You are a consultant at {CONSULTANT} (a fictional firm) writing a proposal deck
for {CLIENT} on "{PROJECT}".

Write the text for EXACTLY {len(SLIDES)} slides, following each brief closely.
Rules:
- Use confident consulting language and your OWN vocabulary.
- Never use a slide's forbidden_words (or close variants) on that slide.
- Never cover something a brief does not ask for.
- 3-5 bullets per slide, each under 25 words. Short speaker notes per slide.
- If needs_table is true, return the content in "table" and keep bullets short.

Slide plan:
{json.dumps(plan, indent=1)}

Return JSON:
{{"slides": [{{"slide_number": 1, "title": "...", "bullets": ["..."], "notes": "...",
              "table": {{"headers": ["..."], "rows": [["..."]]}} or null}}]}}
"""


def check_deck(slides):
    """Find forbidden words Gemini used anyway. Returns a list of problems."""
    problems = []
    if len(slides) != len(SLIDES):
        problems.append(f"Expected {len(SLIDES)} slides, got {len(slides)}")
    for plan, slide in zip(SLIDES, slides):
        text = json.dumps(slide).lower()
        for word in plan.get("avoid", []):
            if word.lower() in text:
                problems.append(f"Slide {plan['n']} uses forbidden word '{word}'")
    return problems


def generate_deck(max_tries=3):
    print("Step 2/4: asking Gemini to write the deck...")
    best, best_problems = None, None
    for attempt in range(1, max_tries + 1):
        # A different cache_tag per attempt, so a retry asks Gemini for a NEW deck
        # instead of getting the same cached (rule-breaking) one back.
        reply = ask_json(deck_prompt(), temperature=0.7, cache_tag=f"deck-attempt-{attempt}")
        slides = reply.get("slides") if isinstance(reply, dict) else reply
        slides = slides if isinstance(slides, list) else []
        problems = check_deck(slides)
        print(f"  attempt {attempt}: {len(problems)} rule violation(s)")
        if best is None or len(problems) < len(best_problems):
            best, best_problems = slides, problems
        if not problems:
            break
    return best, best_problems


def build_deck(slides, path):
    """
    Turn Gemini's slide text into a real .pptx. Slides are placed in the order
    given (position = slide number), and missing/empty fields are tolerated.
    """
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    for i, s in enumerate(slides, start=1):
        title = str(s.get("title") or f"Slide {i}")
        bullets = [str(b) for b in (s.get("bullets") or [])]
        table = s.get("table") or {}
        headers = [str(h) for h in (table.get("headers") or [])]
        rows = [r for r in (table.get("rows") or []) if isinstance(r, list)]

        if i == 1:
            slide = prs.slides.add_slide(prs.slide_layouts[0])  # title layout
            slide.shapes.title.text = title
            slide.placeholders[1].text = "\n".join(bullets)
        elif headers and rows:
            slide = prs.slides.add_slide(prs.slide_layouts[5])  # title only + table
            slide.shapes.title.text = title
            shape = slide.shapes.add_table(len(rows) + 1, len(headers),
                                           Inches(0.6), Inches(1.6), Inches(12), Inches(4))
            for c, h in enumerate(headers):
                shape.table.cell(0, c).text = h
            for r, row in enumerate(rows, start=1):
                for c, val in enumerate(row[:len(headers)]):
                    shape.table.cell(r, c).text = str(val)
            if bullets:  # short caption under the table
                box = slide.shapes.add_textbox(Inches(0.6), Inches(5.9), Inches(12), Inches(1))
                box.text_frame.text = " | ".join(bullets)
        else:
            slide = prs.slides.add_slide(prs.slide_layouts[1])  # title + bullets
            slide.shapes.title.text = title
            body = slide.placeholders[1].text_frame
            body.text = bullets[0] if bullets else ""
            for b in bullets[1:]:
                body.add_paragraph().text = b
            for p in body.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(18)
        slide.notes_slide.notes_text_frame.text = str(s.get("notes") or "")
    prs.save(path)


# ---------------------------------------------------------------------------
# Step 3 + 4: answer key
# ---------------------------------------------------------------------------
def save_answer_key(rfp):
    key = expected_answer_key()
    locations = rfp.get("requirement_locations", {})
    for row in key:
        row["rfp_section"] = locations.get(row["id"], "?")
    (TRUTH / "answer_key.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    with open(TRUTH / "answer_key.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "category", "text", "expected_status",
                                          "expected_slides", "rfp_section"])
        w.writeheader()
        for row in key:
            w.writerow({**row, "expected_slides": ", ".join(map(str, row["expected_slides"]))})
    return key


def main():
    INPUTS.mkdir(parents=True, exist_ok=True)
    TRUTH.mkdir(parents=True, exist_ok=True)

    rfp = generate_rfp()
    (TRUTH / "rfp_content.json").write_text(json.dumps(rfp, indent=2), encoding="utf-8")
    build_rfp_docx(rfp, INPUTS / "rfp_qamar.docx")
    build_rfp_pdf(rfp, INPUTS / "rfp_qamar.pdf")

    slides, problems = generate_deck()
    (TRUTH / "deck_content.json").write_text(json.dumps(slides, indent=2), encoding="utf-8")
    build_deck(slides, INPUTS / "proposal_qamar.pptx")

    print("Step 3/4: checking the deck follows the plan...")
    for p in problems:
        print("  WARNING:", p)
    if not problems:
        print("  OK - no rule violations")

    print("Step 4/4: saving the answer key...")
    key = save_answer_key(rfp)
    counts = {}
    for row in key:
        counts[row["expected_status"]] = counts.get(row["expected_status"], 0) + 1
    print(f"\nDone! Tool inputs in '{INPUTS}/', answer key in '{TRUTH}/'.")
    print(f"Planted answer key: {counts}")


if __name__ == "__main__":
    main()
