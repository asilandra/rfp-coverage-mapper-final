"""
keyword_baseline.py - the comparison method: plain KEYWORD MATCHING (no AI).

This is what the brief warns against. It shows what the tool adds.
For each requirement it takes the content words of the exact RFP wording and
measures, for each slide, the share of those words that appear on the slide
(visible text only, same as the tool). Light stemming ("benchmarked" ->
"benchmark") gives it a fair chance.

  best slide share >= COVERED_AT  -> "Covered"
  best slide share >= PARTIAL_AT  -> "Partially covered"
  otherwise                       -> "Not covered"
  slides cited = every slide with share >= PARTIAL_AT

PRE-REGISTERED: the thresholds below were fixed on 4 October BEFORE the
baseline was ever run, and are not changed afterwards. To be fair, the
evaluation also reports the baseline's BEST possible result with thresholds
tuned on the answer key (an optimistic upper bound for keyword matching).
"""
from evaluation.check_extraction import content_words

COVERED_AT = 0.50
PARTIAL_AT = 0.25


def _stem(word):
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def keywords(text):
    return {_stem(w) for w in content_words(text)}


def slide_shares(requirement, deck):
    """Share of the requirement's keywords found on each slide: {slide_number: share}."""
    wanted = keywords(requirement["source_quote"])
    shares = {}
    for s in deck["slides"]:
        found = keywords(s["visible_text"])
        shares[s["slide_number"]] = len(wanted & found) / len(wanted) if wanted else 0.0
    return shares


def keyword_verdicts(requirements, deck, covered_at=COVERED_AT, partial_at=PARTIAL_AT):
    verdicts = []
    for req in requirements:
        shares = slide_shares(req, deck)
        best = max(shares.values()) if shares else 0.0
        status = "Covered" if best >= covered_at else "Partially covered" if best >= partial_at else "Not covered"
        slides = sorted((n for n, v in shares.items() if v >= partial_at), key=lambda n: -shares[n])
        verdicts.append({"id": req["id"], "requirement": req["requirement"], "status": status,
                         "slides": slides if status != "Not covered" else [], "best_share": round(best, 2)})
    return verdicts
