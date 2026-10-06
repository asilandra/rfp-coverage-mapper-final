"""
extract.py - STAGE 2 of the tool: find every requirement in the RFP.

Principle: "AI proposes, Python verifies."
  1. Gemini reads the RFP (as numbered blocks from parsers.py) and returns each
     requirement with a category, a short restatement, the EXACT quote and the
     block it came from.
  2. Python checks Gemini's work:
       - the quote must really exist in the RFP (catches invented text)
       - the RFP section is taken from the parser, not from Gemini
       - near-duplicate requirements are removed
       - a requirement whose quote is NOT in the RFP is set aside as "unverified"
         (saved and shown for human review, but not passed on), so the tool never
         reports a gap for something the client did not actually ask for
"""
import csv
import difflib
import json
import re
from pathlib import Path

from src.llm import MODEL, ask_json

CATEGORIES = ["Scope", "Deliverable", "Timeline", "Proposal requirement"]

SYSTEM = (
    "You are an experienced bid manager at a management consultancy. "
    "You read client RFPs and list precisely what the client requires, without adding anything."
)

INSTRUCTIONS = """Below is an RFP, split into numbered blocks. Each block shows its ID, type and RFP section.

TASK: list every requirement the client places on the consultant or on the proposal.

CATEGORIES (use exactly one):
- "Scope": work or activities the consultant must carry out
- "Deliverable": tangible outputs the consultant must hand over (reports, portfolios, presentations, language/format of outputs)
- "Timeline": durations, deadlines and milestones of the engagement itself
- "Proposal requirement": what the proposal document must contain or how it must be structured (e.g. CVs, pricing format)

RULES:
1. Keep a single ask together, even if it has several aspects (e.g. "assess the data infrastructure and its governance" is ONE requirement; later stages check each aspect).
2. Split lists of separate items into separate requirements (e.g. "a report, alongside a portfolio" = TWO deliverables).
3. List each requirement ONCE. If an ask is repeated elsewhere (e.g. in evaluation criteria or a summary), cite the place where it is stated as an obligation.
4. Do NOT extract: background or context, evaluation criteria and their weights, submission logistics (how, where or when to submit; clarification questions), confidentiality or legal terms.
5. "source_quote": copy the exact words from ONE block, verbatim, at most about 40 words. Never paraphrase the quote.
6. "requirement": a short, clear restatement (at most 25 words) starting with a verb.

Return JSON only:
{"requirements": [{"category": "...", "requirement": "...", "source_quote": "...", "block_id": "B000"}],
 "skipped_sections": [{"section": "...", "reason": "..."}]}

RFP BLOCKS:
"""


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------
def build_prompt(rfp):
    """Show Gemini every block with its ID, type and section, so it can cite them."""
    lines = [f"[{b['id']} | {b['type']} | {b['section']}] {b['text']}" for b in rfp["blocks"]]
    return INSTRUCTIONS + "\n".join(lines)


# ---------------------------------------------------------------------------
# Python checks on Gemini's answer
# ---------------------------------------------------------------------------
def _norm(text):
    """Lower case, punctuation removed, single spaces: for fair text comparison."""
    text = re.sub(r"[^\w\s%]", " ", str(text).lower())
    return re.sub(r"\s+", " ", text).strip()


def quote_found(quote, text, threshold=0.9):
    """True if (almost) all of the quote appears, in order, inside the text."""
    q, t = _norm(quote), _norm(text)
    if not q:
        return False
    if q in t:
        return True
    matcher = difflib.SequenceMatcher(None, q, t, autojunk=False)
    matched = sum(block.size for block in matcher.get_matching_blocks())
    return matched / len(q) >= threshold


def _category(value):
    """Map Gemini's category onto our four fixed categories."""
    v = str(value).lower()
    for name, key in [("Deliverable", "deliver"), ("Timeline", "time"),
                      ("Proposal requirement", "proposal"), ("Scope", "scope")]:
        if key in v:
            return name
    return "Other"


def _is_duplicate(a, b):
    """Two requirements are duplicates if their statements or quotes are nearly the same."""
    same_text = difflib.SequenceMatcher(None, _norm(a["requirement"]), _norm(b["requirement"])).ratio() >= 0.85
    qa, qb = _norm(a["source_quote"]), _norm(b["source_quote"])
    same_quote = bool(qa and qb) and (qa in qb or qb in qa)
    return same_text or same_quote


def verify(raw_items, rfp):
    """Check each requirement against the real RFP text; return (kept, removed_duplicates, unverified)."""
    blocks = {b["id"]: b for b in rfp["blocks"]}
    order = {b["id"]: i for i, b in enumerate(rfp["blocks"])}
    checked = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        quote = str(item.get("source_quote") or "").strip()
        match = re.search(r"B\d+", str(item.get("block_id") or ""))
        block_id = match.group(0) if match else ""

        if block_id in blocks and quote_found(quote, blocks[block_id]["text"]):
            status = "verified"
        else:
            found = next((b["id"] for b in rfp["blocks"] if quote_found(quote, b["text"])), None)
            if found:
                block_id, status = found, "verified (block corrected)"
            else:
                status = "NOT FOUND in RFP - review"

        checked.append({
            "category": _category(item.get("category")),
            "requirement": str(item.get("requirement") or "").strip(),
            "source_quote": quote,
            "block_id": block_id if block_id in blocks else "",
            "section": blocks[block_id]["section"] if block_id in blocks else "",
            "quote_check": status,
        })

    # set aside requirements whose quote is not in the RFP
    unverified = [r for r in checked if r["quote_check"].startswith("NOT FOUND")]
    checked = [r for r in checked if not r["quote_check"].startswith("NOT FOUND")]

    # keep RFP order, then remove near-duplicates (first one wins)
    checked.sort(key=lambda r: order.get(r["block_id"], 10**6))
    kept, removed = [], []
    for req in checked:
        twin = next((k for k in kept if _is_duplicate(k, req)), None)
        if twin:
            removed.append({**req, "duplicate_of": twin["requirement"]})
        else:
            kept.append(req)
    for i, req in enumerate(kept, start=1):
        req["id"] = f"R{i:02d}"
    return kept, removed, unverified


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def extract_requirements(rfp):
    """Parsed RFP in, verified requirement list out."""
    reply = ask_json(build_prompt(rfp), system=SYSTEM, temperature=0.0, cache_tag="extract-v1")
    if isinstance(reply, list):
        reply = {"requirements": reply}
    raw = reply.get("requirements") if isinstance(reply, dict) else None
    if not isinstance(raw, list) or not raw:
        raise ValueError("Gemini returned no requirements.")
    kept, removed, unverified = verify(raw, rfp)
    if not kept:
        raise ValueError("None of Gemini's requirements could be verified against the RFP text.")
    return {
        "rfp_source": rfp["source"],
        "model": MODEL,
        "requirements": kept,
        "removed_duplicates": removed,
        "unverified": unverified,
        "skipped_sections": reply.get("skipped_sections") or [],
    }


def save_requirements(result, folder="output"):
    """Save the full result as JSON, and the requirement list as CSV."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "requirements.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    fields = ["id", "category", "requirement", "section", "block_id", "source_quote", "quote_check"]
    with open(folder / "requirements.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(result["requirements"])
    return folder / "requirements.json", folder / "requirements.csv"
