"""
run_evaluation.py - reproduce the final evaluation with one command.

    python run_evaluation.py

Runs the tool on the synthetic test set (from the cache: no API calls needed),
then scores it against the answer key and the keyword baseline.
Output: output/evaluation_report.md (+ .json)

This is the ONLY entry point that reads test_data/ground_truth/ (via evaluation/).
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")   # Windows: print "?" instead of crashing on special characters

from evaluation.final_evaluation import compare, write_report
from src.pipeline import run_pipeline

RFP = "test_data/inputs/rfp_qamar.pdf"
DECK = "test_data/inputs/proposal_qamar.pptx"


def main():
    run = run_pipeline(RFP, DECK, "output")
    result = compare(run["verdicts"], run["extraction"]["requirements"], run["deck"], run["extraction"], run["judge_model"])
    path = write_report(result, "output/evaluation_report.md")
    t = result["tool"]
    print(f"\nFinal score (18 planted requirements, judge model {run['judge_model']}):")
    print(f"  1. Gaps caught:     {t['gaps_caught']}")
    print(f"  2. Status accuracy: {t['status_accuracy']}")
    print(f"  3. False alarms:    {t['false_alarms']}")
    print(f"  4. Slide accuracy:  {t['slide_accuracy']}")
    print(f"  Keyword traps fooled: {t['traps_fooled']}/{result['traps_total']}")
    print(f"Full comparison with the keyword baseline: {path}")


if __name__ == "__main__":
    main()
