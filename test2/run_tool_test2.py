"""
run_tool_test2.py - runs the PUBLISHED tool on Test 2 with an explicitly chosen model.

    python -m test2.run_tool_test2 <tool_model>

Same functions, in the same order, as src/pipeline.py run_pipeline(); the only difference is
that the judge's EXISTING `models` parameter is set to one chosen model (and extraction uses
the same model via GEMINI_MODEL, with no fallback). This keeps the tool's model different from
the model that wrote the Test 2 documents. Writes ONLY to output_test2/.
"""
import json
import sys
from pathlib import Path

from src import llm
from src.extract import extract_requirements, save_requirements
from src.judge import save_judgements
from src.parsers import parse_deck, parse_rfp
from src.pipeline import judge_with_one_model
from src.report import write_report
from src.retrieve import SlideRetriever

RFP = "test_data_2/inputs/rfp_test2.pdf"
DECK = "test_data_2/inputs/proposal_test2.pptx"
OUT = "output_test2"


def main(tool_model):
    if llm.MODEL != tool_model or llm.FALLBACK_MODELS:
        raise SystemExit(f"Set GEMINI_MODEL={tool_model} and GEMINI_FALLBACK_MODELS='' before running (got {llm.MODEL}, {llm.FALLBACK_MODELS})")
    Path(OUT).mkdir(exist_ok=True)
    print("[1/5] Parsing the RFP and the deck...")
    rfp, deck = parse_rfp(RFP), parse_deck(DECK)
    print(f"      RFP: {len(rfp['blocks'])} blocks · deck: {deck['slide_count']} slides")
    print(f"[2/5] Extracting requirements with {tool_model}...")
    extraction = extract_requirements(rfp)
    extraction_model = str(llm.last_model_used).replace("cache: ", "")
    save_requirements(extraction, OUT)
    print(f"      {len(extraction['requirements'])} requirements")
    print("[3/5] Ranking slides by meaning...")
    retriever = SlideRetriever(deck)
    print(f"      {retriever.method}")
    print(f"[4/5] Judging coverage with {tool_model} only...")
    verdicts, judge_model = judge_with_one_model(extraction["requirements"], deck, retriever, models=[tool_model])
    save_judgements(verdicts, OUT)
    print("[5/5] Writing the Excel report...")
    write_report(verdicts, deck, rfp, f"{OUT}/coverage_report.xlsx", judge_model=judge_model,
                 retrieval_method=retriever.method, unverified=extraction.get("unverified", []))
    info = {"extraction_model": extraction_model, "judge_model": judge_model,
            "how_run": "published functions, same order as run_pipeline(); judge models parameter = [tool model]"}
    Path(f"{OUT}/run_info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    gaps = [v for v in verdicts if v["status"] != "Covered"]
    print(f"\nDone: {len(verdicts)} requirements, {len(gaps)} gap(s). Extraction model: {extraction_model} | judge model: {judge_model}")


if __name__ == "__main__":
    main(sys.argv[1])
