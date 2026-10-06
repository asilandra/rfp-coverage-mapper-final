# RFP vs Proposal Coverage Mapper

A Python tool that checks whether a **proposal deck (PPTX)** covers everything a client's **RFP (PDF or Word)** asks for, and produces a colour-coded **Excel report** showing:

1. every scope item, deliverable, timeline and proposal requirement in the RFP,
2. which slide(s) address it, with the exact slide text as evidence,
3. everything the deck does **not** fully address (the gaps to fix before submission).

It judges **meaning, not shared keywords**: the same idea is often phrased differently in an RFP and a proposal, and shared words can be misleading.

*Built as a technical exercise on a real consulting workflow problem. All test documents are synthetic: no real client data was used.*

---

## Results

Both tests were built from an **answer key written before the documents existed**, with paraphrased slides and keyword "trap" slides. In each test, one model judged every requirement.

### Test 1: official test set (logistics; 18 planted requirements: 10 covered, 4 partial, 4 missing)

| Metric | **This tool** | Keyword matching (thresholds fixed in advance) | Keyword matching, best possible (tuned on the answers) |
|---|---|---|---|
| **1. Gaps caught** (primary) | **8/8** | 8/8 (by flagging everything) | 6/8 |
| 2. Status accuracy | **16/18** | 6/18 | 12/18 |
| 3. False alarms (lower is better) | **2/10** | 10/10 | 3/10 |
| 4. Correct slide cited | **18/18** | 12/18 | 12/18 |
| Keyword traps fooled (lower is better) | **0/5** | 1/5 | 1/5 |

Judge: `gemini-3.5-flash-lite`. Both disagreements are *stricter* than the answer key (the safer direction for a pre-submission check). Details: [`output/evaluation_report.md`](output/evaluation_report.md).

### Test 2: unseen scenario, live run (healthcare; 20 planted requirements: 11 covered, 5 partial, 4 missing)

A second scenario the tool had never seen, in a different industry, with an RFP that rewords every requirement. To reduce the risk of an AI judging its own writing, **the documents were written by a different model (`gemini-3.1-flash-lite`) from the one running the tool (`gemini-3.5-flash-lite`)**. The judge was not changed.

| Metric | **This tool** | Keyword matching (thresholds fixed in advance) | Keyword matching, best possible (tuned on the answers) |
|---|---|---|---|
| **1. Gaps caught** (primary) | **9/9** | 9/9 (by flagging everything) | 4/9 |
| 2. Status accuracy | **16/20** | 4/20 | 12/20 |
| 3. False alarms (lower is better) | **2/11** | 11/11 | 1/11 |
| 4. Correct slide cited | **18/20** | 12/20 | 15/20 |
| Keyword traps fooled (lower is better) | **1/4** | 1/4 | 4/4 |

Requirement extraction found **20/20** planted requirements. Of the 4 disagreements, 3 come from generated slides that were vaguer than the plan (e.g. a team slide giving an advisor's role but no name); 1 is a genuine judge error (an "Arabic-speaking analyst" was partly credited towards "report in Arabic"; the gap was still flagged). The answer key was not changed after seeing the results. Details: [`output_test2/test2_report.md`](output_test2/test2_report.md).

---

## How it works

```
 RFP (PDF / Word) + deck (PPTX)
          |
 [1] Parse ............... plain Python (no AI): RFP -> blocks tagged with their section; deck -> one record per slide
          |
 [2] Extract requirements  Gemini lists every requirement with an exact RFP quote -> Python verifies each quote
          |
 [3] Rank slides ......... local embedding model ranks slides by meaning (free, runs on CPU, no data leaves the machine)
          |
 [4] Judge coverage ...... Gemini decides Covered / Partially covered / Not covered, with an evidence quote
          |                -> Python verifies the quote is on the cited slide
 [5] Excel report ........ Summary, Coverage, Gaps, Slide map, Matrix
```

**Three principles**

- **AI proposes, Python verifies.** Every requirement must quote the RFP word for word, and every verdict must quote the slide; code checks both. Requirements whose quote can't be found are set aside instead of being judged, and doubtful verdicts are flagged for review, never silently fixed.
- **AI only where judgement is needed.** Reading files and writing Excel are deterministic Python.
- **Measure, don't assume.** Retrieval was measured before it was trusted: a top-5 shortlist missed the right slide for 1 of 14 requirements, so on decks of up to 25 slides the ranking only *orders* the slides and the judge reads all of them.

| Stage | File | Notes |
|---|---|---|
| Shared AI module | `src/llm.py` | The only file that calls Gemini: key loading, JSON answers, retries with backoff, backup model, 6 s pacing, disk cache, clear error messages |
| 1. Parse | `src/parsers.py` | pdfplumber, python-docx, python-pptx; refuses to read `ground_truth/` |
| 2. Extract | `src/extract.py` | One Gemini call, temperature 0; quote verification, de-duplication |
| 3. Rank slides | `src/retrieve.py` | sentence-transformers `all-mpnet-base-v2`, cosine similarity, visible slide text only |
| 4. Judge | `src/judge.py` | One Gemini call per requirement, temperature 0; evidence verification |
| 5. Report | `src/report.py` | openpyxl; live Excel formulas for the totals |
| Pipeline | `src/pipeline.py` | Connects stages 1–5; **one model per judge run** (restarts the whole run on the backup model instead of mixing models); reuses a complete cached run for reproducibility |

---

## Quick start

Developed and verified on **Linux (Kaggle, Python 3.13)**; reviewed for Windows and macOS compatibility (see Limitations).

```bash
pip install -r requirements.txt
```

`requirements.txt` pins the exact library versions the tool was verified with. The first run downloads the embedding model (~420 MB), so an internet connection is needed once.

### Reproduce the results above (no API key needed)

The cache folders contain every Gemini answer used for the results, so these commands make **no API calls**:

```bash
python run_mapper.py --rfp test_data/inputs/rfp_qamar.pdf --deck test_data/inputs/proposal_qamar.pptx
python run_evaluation.py          # Test 1: scores the tool and writes output/evaluation_report.md
python -m test2.replay_test2      # Test 2: replays the unseen-scenario run and its scoring
```

### Run it on your own documents

1. Get a Gemini API key (Google AI Studio).
2. Copy `.env.example` to `.env` and paste your key there. **`.env` is excluded from Git: never commit it.**
3. Run:

```bash
python run_mapper.py --rfp path/to/rfp.pdf --deck path/to/proposal.pptx --out output
```

**What a live run costs:** about one Gemini call to extract the requirements plus one per requirement (≈ 22 calls for ~21 requirements), spaced 6 seconds apart for the free tier: a few minutes (Test 2: 21 calls in 2.5 minutes). Answers are cached, so a rerun of the same documents takes seconds and makes no calls.

**If something goes wrong,** the tool prints one `ERROR:` line saying what to do:

- **Busy (503) or quota used up (429):** free-tier limits reset daily. Wait and run again, try another model, or use a paid key. Cached results keep working without any calls.
- **Model not available (404):** Google retires models over time (`gemini-2.5-flash` was retired during this project). Run `python check_setup.py` to list the models your key can use, then set `GEMINI_MODEL=<model>` in `.env`.
- **Invalid key:** check `GEMINI_API_KEY` in `.env`.
- **Wrong or unreadable file:** use `.pdf`/`.docx` for the RFP and `.pptx` for the deck; scanned PDFs (images of text) are not supported. On Windows, close the Excel report before running again.

> **Confidentiality:** on Gemini's free tier, prompts may be used by Google. Use synthetic documents only, or switch to an enterprise or private model for real client material. Because every AI call goes through `src/llm.py`, that is a one-file change.

---

## Repository structure

```
run_mapper.py              the tool in one command
run_evaluation.py          reproduce the Test 1 scoring
check_setup.py             check the API key and list the available models
src/                       the tool (stages 1-5, shared AI module, pipeline)
evaluation/                Test 1 scoring code: the ONLY code that reads test_data/ground_truth/
synthetic/                 how the Test 1 set was designed and generated (scenario, generator, checklist)
test_data/inputs/          Test 1: synthetic RFP (.pdf and .docx) and proposal deck (.pptx)
test_data/ground_truth/    Test 1: the answer key (used only by evaluation/)
output/                    Test 1 official results: coverage_report.xlsx, evaluation_report.md, requirements, verdicts
cache/                     cached Gemini answers that make Test 1 reproducible
test2/                     Test 2: scenario (answer key first), generator, runner, scoring, replay
test_data_2/               Test 2 documents and answer key (incl. which model wrote them)
output_test2/              Test 2 results: coverage_report.xlsx, test2_report.md, verdicts
cache_test2/               cached Gemini answers that make Test 2 reproducible
notebooks/                 the Kaggle notebooks run each day (snapshots; src/ holds the final code)
DESIGN_DECISIONS.md        every design decision, with reasons and alternatives
```

---

## The synthetic test sets

- **Test 1** (`synthetic/scenario.py`): fictional client *Qamar Logistics Group*, fictional consultancy *Meridian Advisory*; 18 requirements and a 15-slide plan. Slides paraphrase with *forbidden words* (e.g. "proof-of-concept pilots" became "two rapid minimum viable products"), partial slides cover only part of a requirement, and **trap slides** share keywords without addressing it (firm values mentioning "ethical"; fees "benchmarked" against the market; case studies for other clients).
- **Test 2** (`test2/scenario2.py`): fictional client *Falaj Health Partners*, fictional consultancy *Tessera Advisory*; 20 requirements, a 16-slide plan, new paraphrases and 4 new traps (the firm's own data-protection certification; a "benchmarking database" capability claim; an Arabic-speaking team vs deliverables in Arabic; invoices "within 30 days of award").
- In both, Gemini wrote the text and Python built the files. `python -m synthetic.generate_test_data` regenerates a **new** Test 1 set (needs an API key) and **overwrites** `test_data/`; the official sets are the ones in this repository.

## How the evaluation works, and why it's fair

- Scored on the **planted requirements only**; genuine extra requirements the tool finds (3 in Test 1) are reported but not scored, because each answer key was fixed before its documents existed.
- **Gap detection is the primary metric**, read together with false alarms (a method that flags everything also "catches" every gap).
- The keyword baseline uses the same requirements and slide text, light stemming, and thresholds (0.50 / 0.25) **fixed before it was first run**. Its best possible score, with thresholds tuned on the answers, is also reported.
- The judge's prompt was **not** changed after seeing any results (to avoid tuning on the test set).

## Limitations and future work

- **Two synthetic scenarios** (18 and 20 scored requirements; one verdict ≈ 5 points). Next: more unseen scenarios, human-written documents, and a separate development set.
- **Same model family:** in Test 2 the writer and the judge were different models, but both Gemini. In Test 1, the same model (`gemini-3.5-flash-lite`) happened to write the documents (as the backup model on day 1) and to judge them. A fully independent check would use another provider's model or human-written documents.
- **The judge leans strict** (2 false alarms in each test, on wording details); calibration on a separate development set is future work.
- **A known judge error** (Test 2, D4): the verdict's status contradicted its own reasoning. Next step: automatically flag verdicts whose reasoning and status disagree, for human review.
- **Run-to-run variation:** the same model and prompt changed one verdict between two runs, even at temperature 0. Results are cached for reproducibility; a next step is several runs with a majority vote.
- **Not read:** speaker notes (by design: the client never sees them), text inside images, charts or SmartArt, scanned PDFs (would need OCR), old `.doc` / `.ppt` files.
- **Word vs PDF:** the Word version of the Test 1 RFP was tested live, end to end. Its text is 99.95% similar to the PDF's (the PDF reader joins the title and reference line), so it cannot be replayed from the PDF run's cache.
- **Platforms:** developed and verified on Linux (Kaggle). The code was reviewed for Windows and macOS (file paths, text encoding, special characters, locked Excel files), but not yet run there; a real Windows/macOS test is future work. Replaying from the cache assumes the slide ranking comes out in the same order; if another machine orders two near-identical slides differently, the tool asks for an API key rather than giving a wrong result.
- **Untested at scale:** decks over 25 slides (retrieval then filters to the top 25) and very long RFPs (currently one extraction call).

## How this was built

I used AI assistance to design and build the tool. I chose and adapted the architecture, made the key methodological decisions, and verified every stage myself. Development ran in daily Kaggle notebooks (`notebooks/`), with automatic ✅/❌ checks at every step and every result re-checked from the downloaded outputs. Gemini has two separate roles here: it wrote the synthetic test documents, and it is the language model inside the tool.

*Author: Asya · October 2026*
