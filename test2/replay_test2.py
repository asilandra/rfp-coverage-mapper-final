"""
replay_test2.py - reproduce the Test 2 results from its cache (no API key needed).

    python -m test2.replay_test2

Runs the tool on the Test 2 documents with gemini-3.5-flash-lite answers taken from
cache_test2/ (no API calls), then scores it. Rewrites output_test2/ with identical verdicts.
"""
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")   # Windows: print "?" instead of crashing on special characters

TOOL_MODEL = "gemini-3.5-flash-lite"
os.environ["LLM_CACHE_DIR"] = "cache_test2"     # Test 2's own cache (never the official cache/)
os.environ["GEMINI_MODEL"] = TOOL_MODEL
os.environ["GEMINI_FALLBACK_MODELS"] = ""

from test2 import evaluate_test2, run_tool_test2  # noqa: E402  (imported after the settings above)

if __name__ == "__main__":
    try:
        run_tool_test2.main(TOOL_MODEL)
    except (RuntimeError, ValueError, FileNotFoundError) as e:
        sys.exit(f"ERROR: {e}")
    print()
    evaluate_test2.main()
