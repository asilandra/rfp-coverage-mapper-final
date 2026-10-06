"""
run_mapper.py - run the whole tool with one command.

    python run_mapper.py --rfp test_data/inputs/rfp_qamar.pdf --deck test_data/inputs/proposal_qamar.pptx

Input:  an RFP (.pdf or .docx) and a proposal deck (.pptx)
Output: output/coverage_report.xlsx (plus requirements and verdicts as JSON/CSV)
Needs:  GEMINI_API_KEY in a .env file or the environment (or Kaggle Secrets).
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")   # Windows: print "?" instead of crashing on special characters

import argparse

from src.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="Check which RFP requirements a proposal deck covers.")
    parser.add_argument("--rfp", required=True, help="RFP file (.pdf or .docx)")
    parser.add_argument("--deck", required=True, help="Proposal deck (.pptx)")
    parser.add_argument("--out", default="output", help="Output folder (default: output)")
    args = parser.parse_args()
    try:
        result = run_pipeline(args.rfp, args.deck, args.out)
    except PermissionError as e:
        if e.filename:      # a file could not be written (Windows locks files that are open in Excel)
            sys.exit(f"ERROR: cannot write {e.filename}. If the Excel report is open (e.g. in Excel on Windows), close it and run again.")
        sys.exit(f"ERROR: {e}")   # e.g. the safety guard refusing to read the answer key
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        sys.exit(f"ERROR: {e}")
    gaps = [v for v in result["verdicts"] if v["status"] != "Covered"]
    print(f"\nDone: {len(result['verdicts'])} requirements, {len(gaps)} gap(s). Report: {result['report_path']}")


if __name__ == "__main__":
    main()
