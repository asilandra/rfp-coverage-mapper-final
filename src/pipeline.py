"""
pipeline.py - connects the five stages into one run:

  [1] parse  ->  [2] extract requirements  ->  [3] rank slides  ->  [4] judge  ->  [5] Excel

Judging uses ONE model for every requirement (decision 50, agreed by Asya):
try the main model for the whole run; if it keeps failing, restart the WHOLE run
with the next model. Models are never mixed within one run, because
consistency matters more than model strength.

Reproducibility: if a COMPLETE set of verdicts from one model is already in the
cache, that set is reused first (no API calls), so rerunning gives the same
final result even if a different model happens to be available on the day.
"""
from src import llm
from src.extract import extract_requirements, save_requirements
from src import judge as judge_module
from src.judge import judge_all, save_judgements
from src.parsers import parse_deck, parse_rfp
from src.report import write_report
from src.retrieve import SlideRetriever

JUDGE_MODELS = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]   # in order of preference
JUDGE_CACHE_TAG = "judge-final"                                # separate from Day 4's mixed run
JUDGE_ATTEMPTS = 4                                             # patient retries: waits of 10s, 20s, 40s


def fully_cached(model, requirements, deck, retriever, cache_tag=JUDGE_CACHE_TAG):
    """True if every requirement already has a cached verdict from this model."""
    slides_by_number = {s["slide_number"]: s for s in deck["slides"]}
    saved_model = llm.MODEL
    llm.MODEL = model                      # the cache fingerprint includes the model name
    try:
        return all(llm._cache_file(judge_module.build_prompt(r, slides_by_number, retriever.rank(r)),
                                   judge_module.SYSTEM, 0.0, cache_tag).exists() for r in requirements)
    finally:
        llm.MODEL = saved_model


def judge_with_one_model(requirements, deck, retriever, models=JUDGE_MODELS,
                         cache_tag=JUDGE_CACHE_TAG, progress=print):
    """Return (verdicts, model). All verdicts come from the same model, or an error is raised."""
    saved = (llm.MODEL, list(llm.FALLBACK_MODELS), llm.ATTEMPTS_PER_MODEL, llm._main_model_busy)
    cached = [m for m in models if fully_cached(m, requirements, deck, retriever, cache_tag)]
    if cached:
        progress(f"A complete cached run by {cached[0]} exists: reusing it (no API calls, reproducible result).")
        models = cached[:1]
    last_reason = ""
    try:
        for model in models:
            # one model only: no automatic backup inside the run
            llm.MODEL, llm.FALLBACK_MODELS, llm.ATTEMPTS_PER_MODEL, llm._main_model_busy = model, [], JUDGE_ATTEMPTS, False
            progress(f"Judging all {len(requirements)} requirements with {model} only...")
            try:
                verdicts = judge_all(requirements, deck, retriever, progress=progress, cache_tag=cache_tag)
            except RuntimeError as e:          # this model kept failing (busy / rate-limited / unavailable)
                last_reason = str(e)
                progress(f"{model} kept failing ({last_reason[:120]}). Restarting the WHOLE run with the next model.")
                continue
            used = {str(v["model"]).replace("cache: ", "") for v in verdicts}
            if used != {model}:
                raise RuntimeError(f"Consistency check failed: verdicts came from {used}, expected only {model}")
            return verdicts, model
        raise RuntimeError(f"Every judge model failed: {models}. Last reason: {last_reason}")
    finally:
        llm.MODEL, llm.FALLBACK_MODELS, llm.ATTEMPTS_PER_MODEL, llm._main_model_busy = saved


def run_pipeline(rfp_path, deck_path, out_folder="output", progress=print):
    """The whole tool: RFP + deck in, Excel report out. Returns a dict with every intermediate result."""
    progress("[1/5] Parsing the RFP and the deck...")
    rfp, deck = parse_rfp(rfp_path), parse_deck(deck_path)
    progress(f"      RFP: {len(rfp['blocks'])} blocks · deck: {deck['slide_count']} slides")

    progress("[2/5] Extracting requirements (Gemini proposes, Python verifies)...")
    extraction = extract_requirements(rfp)
    save_requirements(extraction, out_folder)
    requirements = extraction["requirements"]
    progress(f"      {len(requirements)} requirements")

    progress("[3/5] Ranking slides by meaning (local embedding model)...")
    retriever = SlideRetriever(deck)
    progress(f"      {retriever.method}")

    progress("[4/5] Judging coverage (one model for the whole run)...")
    verdicts, judge_model = judge_with_one_model(requirements, deck, retriever, progress=progress)
    save_judgements(verdicts, out_folder)

    progress("[5/5] Writing the Excel report...")
    report_path = write_report(verdicts, deck, rfp, f"{out_folder}/coverage_report.xlsx",
                               judge_model=judge_model, retrieval_method=retriever.method,
                               unverified=extraction.get("unverified", []))
    progress(f"      Saved {report_path}")
    return {"rfp": rfp, "deck": deck, "extraction": extraction, "retriever": retriever,
            "verdicts": verdicts, "judge_model": judge_model, "report_path": report_path}
