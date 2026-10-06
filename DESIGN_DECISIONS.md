# Design decisions

Every important technical and methodological choice made while building and testing the tool, with the reason and the alternative that was considered.
Decisions marked **(Agreed by Asya)** or **(Asya)** are methodological decisions about how the results are measured and reported.

| # | Decision | Reason | Alternative considered |
|---|---|---|---|
| 1 | Answer key defined before the documents | Makes accuracy measurable | Generate freely, then label by hand (slow, unreliable) |
| 2 | Paraphrases (forbidden words) and trap slides in the test data | Targets the two keyword-matching failure modes in the brief | Plain test data (would not show the tool's value) |
| 3 | Gemini writes the content, Python builds the files | Valid files, controlled structure | AI generates the files directly |
| 4 | RFP in both Word and PDF | Tests both input types required by the brief | One format only |
| 5 | Forbidden-word check with up to 3 regenerations | Validates the AI output instead of trusting it | Manual checking only |
| 6 | Separate `inputs/` and `ground_truth/` folders | Prevents data leakage | One folder |
| 7 | All LLM calls in one module (`src/llm.py`) | One place for key, retries, cache, model; easy provider switch | Gemini calls scattered across files |
| 8 | Key in Kaggle Secrets / `.env`, `.env` in `.gitignore` | Never exposed in code or on GitHub | Key written in the notebook (unsafe) |
| 9 | Disk cache keyed on model + prompt + settings | Free reruns, reproducible demo | No cache (uses quota, results change) |
| 10 | JSON mode plus exponential backoff | Machine-readable answers; survives the free tier's limits | Free text with parsing |
| 11 | Pinned models: `gemini-3.8-flash`, backup `gemini-3.5-flash-lite` | Reproducible; `gemini-2.5-flash` retired for new users | "-latest" aliases (can change silently) |
| 12 | Automatic fallback after 3 tries, printing the real error | The main model was overloaded (503) | Manual model switching |
| 13 | Fictional consultancy ("Meridian Advisory") | Avoids inventing claims about a real firm | Use a real consultancy's name |
| 14 | All-in-one Kaggle notebook (`%%writefile` cells) | Removed dataset and nested-folder problems | Upload code as a Kaggle dataset |
| 15 | Automatic ✅/❌ checklist on the real files | Fast, objective confirmation of completeness | Manual inspection |
| 16 | A diagnostic cell, and ✅/❌ STEP lines for every cell | Problems found immediately, without reading code | Reading raw errors |
| 17 | Notebooks tested end to end in a real Jupyter kernel before delivery | Catches notebook-only errors (e.g. empty `%%writefile`) | Testing the Python files only |
| 18 | Official test set = the interactive-session zip of 3 Oct (cache included) | Consistent, reviewed data for all later stages | Regenerating data each run |
| 19 | No AI for parsing (pdfplumber, python-docx, python-pptx) | Deterministic, free, instant, repeatable | LLM reads files directly (slower, uses quota, may alter text) |
| 20 | RFP stored as **blocks** tagged with type and section | Traceability (where each requirement came from); helps skip evaluation criteria on Day 3 | One plain text string |
| 21 | Rebuild PDF paragraphs with rules (numbered heading, bullet symbol, short line ending in punctuation) | PDFs store lines, not paragraphs | Keep raw lines (fragmented sentences) |
| 22 | Remove `(cid:NN)` symbols; a leading one marks a bullet | pdfplumber can't decode the bullet symbol | Leave the symbols (noise for later stages) |
| 23 | Speaker notes kept separate from visible slide text | The client never sees notes; Day 4 decides explicitly whether they count | Merge notes into the slide text |
| 24 | Table rows kept on separate lines | Timelines and fees are often tables; merged rows lose meaning | Flatten each table into one line |
| 25 | Safety guard runs **first**, in both `parse_rfp` and `parse_deck` | Leakage protection must not depend on the file type | Guard after the format check (bug 2) |
| 26 | Parsed output saved as JSON in `output/parsed/` | Inspectable evidence; reusable by later stages | Keep in memory only |
| 27 | New dataset `rfp-coverage-mapper-final`; one notebook per day | Clean single source of the official test set; notebooks match log sections | New version of the old dataset; one growing notebook |
| 28 | Failed steps stop Run All on purpose (`StepFailed`) | Prevents a chain of confusing follow-on errors | Let Run All continue after a failure |
| 29 | "AI proposes, Python verifies" for extraction | Trustworthy output: every requirement checked against the real RFP | Trust the LLM's list as is |
| 30 | Exact quote + block ID required for every requirement | Traceability for analysts; makes invented text detectable | Paraphrased requirements only |
| 31 | Quote check: normalised substring, or ≥90% in-order match | Tolerates tiny copying differences without accepting invented text | Exact match only (too strict) or no check |
| 32 | Unverified requirements set aside, not judged | Prevents fake "gaps" in the Excel | Flag but still judge them |
| 33 | Keep compound asks together; split lists of separate items | Enables partial-coverage judging (S3, D3); separate documents checked separately | Split every "and" (loses partials) or never split (merges D1/D2) |
| 34 | Skip background, evaluation criteria, submission logistics, confidentiality | They are not things a deck must address; avoids duplicates | Extract everything, filter later |
| 35 | Temperature 0 for extraction | Consistency over creativity | Default temperature |
| 36 | Evaluation code in a separate `evaluation/` folder | Only the "exam marker" reads the answer key | Mix evaluation into the tool |
| 37 | Transparent word-overlap matching for evaluation (≥0.5) | Explainable, checkable by a person; no LLM grading an LLM | LLM-based matching |
| 38 | Self-contained daily notebooks (rewrite earlier modules) | No new dataset upload needed each day | Upload a new dataset version daily |
| 39 | **(Agreed by Asya; to be implemented on Day 5)** Score only the 18 planted requirements; report extras separately | Answer key fixed before the documents; labelling extras after seeing the results would be biased. Same principle as a dissertation: define how success is measured before looking at the results | Add the 3 extras to the answer key now |
| 40 | Retrieval **orders** slides; the judge sees all of them on decks ≤ 25 slides | Measured: a top-5 shortlist missed 1 of 14 correct slides; a hidden slide = a false gap | Hard top-5 shortlist |
| 41 | Local embedding model `all-mpnet-base-v2` (sentence-transformers, CPU) | Free, private, deterministic; ranked correct slides higher than MiniLM in the measurement | MiniLM (smaller); Gemini embeddings (quota, data leaves) |
| 42 | Whole-slide embeddings | Line-level scoring tested; no improvement | Score each bullet separately |
| 43 | Judge reads **visible slide text only** (no speaker notes) | The client never sees notes | Include notes |
| 44 | One Gemini call per requirement, temperature 0, cache tag `judge-v1` | Focused reasoning, evidence per verdict, free reruns | One call for all requirements |
| 45 | Judge rules written in **general terms** | Avoid "teaching to the test" | Name the specific trap types/slides |
| 46 | Python verifies each verdict (status, slides shown, evidence ≥ 85% on a cited slide); doubtful ones flagged, never silently fixed | Trustworthy, checkable output | Trust the verdict as is |
| 47 | 6-second spacing between real API calls | Stay under the free tier's requests-per-minute limit | No pacing (risk of 429 errors) |
| 48 | Sticky backup model after 3 failures | Avoid 30 s waits per call when the main model is busy. *Side effect: mixed-model runs* | Retry the main model every time |
| 49 | Evaluation metrics: gaps caught, false alarms, status accuracy, slide accuracy, retrieval rank | "Gaps caught" is what matters most for a pre-submission check | Accuracy only |
| 50 | **(Agreed by Asya)** Final score from a judge run with **one model for all 21 requirements**: try `gemini-3.8-flash` for the whole run; if it keeps being busy, run the **entire** judge with `gemini-3.5-flash-lite` instead (never switch mid-run). Record the model used; cache the results so the final score is reproducible | Consistency matters more than model strength; removes the Day 4 model confound. Day 4's mixed run stays recorded | Score the mixed run; switch models mid-run |
| 51 | **(Agreed by Asya)** Do not change the judge's prompt after seeing the results; report the honest result; list "calibrating strictness on a separate development set" as future work | Changing it now = tuning on the test set (overfitting) | Loosen the prompt to fix D1/T2 |
| 52 | **(Agreed by Asya)** Day 5 reporting leads with **gap detection** (primary metric), then status accuracy, false alarms, slide accuracy and the keyword-baseline comparison | Catching gaps is the tool's main purpose | Lead with overall accuracy |
| 53 | Single-model judge run with **whole-run restart** on the next model, plus a consistency check | Implements decision 50 in code | Backup inside the run (mixes models) |
| 54 | **Cache-first reuse** of a complete single-model run | Final score reproducible even if a different model is available later | Always try the preferred model first |
| 55 | Separate cache tag `judge-final`; 4 attempts per call in the final run | Never mixes with Day 4's cached answers; more patience before giving up on a model | Reuse `judge-v1` |
| 56 | Excel report: 5 sheets, Arial, colour-coded statuses, **live formulas** for totals, evidence + RFP wording on every row, print-friendly | Answers the brief's 3 questions; checkable by an analyst; totals update on manual edits | Plain CSV; hard-coded totals |
| 57 | The report includes **all 21** requirements (incl. extras); the evaluation scores only the 18 planted | The tool reports what the RFP asks; scoring follows decision 39 | Drop extras from the report |
| 58 | Keyword baseline on the exact RFP wording, light stemming, **thresholds 0.50/0.25 fixed before its first run**; also report its best possible (tuned) score | Fair comparison; no straw man | Only the tuned baseline, or only the untuned one |
| 59 | Read gap detection **together with** false alarms | Flagging everything trivially "catches" every gap | Gap detection alone |
| 60 | One-command tool `run_mapper.py` | Simple demo; the form a team would use | Notebook only |
| 61 | Live demo runs **from the cache** | Free-tier quota and server load make live calls unreliable | Live API calls during the presentation |
| 62 | README states the work neutrally ("a real consulting workflow problem"); no company name in any public file | The repo is public (Asya's decision) | Name the company |
| 63 | **(Asya)** Pre-submission testing: one item at a time; the verified GitHub version is the frozen baseline; new tests in separate folders; code changes only for genuine bugs, explained first; after any change, re-verify the official 21 verdicts | Momentum without risking the verified result | Ad-hoc fixes |
| 64 | **(Asya)** Test 2 on an unseen scenario, live, answer key written first, judge prompt unchanged; reported whatever the result | Tests generalisation honestly | Only Test 1 |
| 65 | **(Asya)** Writer model ≠ tool model in Test 2, both recorded | Reduce self-preference bias | Same model for both |
| 66 | Test 2 answer key **not changed** after seeing results, even where the generated slides diverged from the plan | Same principle as decision 39 | Relabel S6, C1, C3 |
| 67 | **(Asya)** Record the D4 judge error as a known limitation; do not change the judge now. Next step: automatically flag verdicts whose reasoning and status disagree, for human review, validated on a new unseen scenario | Fixing it now would be tuning on Test 2 | Patch the judge prompt now |
| 68 | **(Asya)** Add Test 2 to the final repo in its own folders and one slide to the presentation; Test 1's official results unchanged | Shows generalisation honestly without touching the verified baseline | Replace Test 1 with Test 2 |
| 69 | **(Asya)** Fold the useful parts of item 2 (Word RFP run, clear error messages) into item 5; item 1b optional | Keep momentum towards submission | Separate sessions for each |
| 70 | Pin the 9 libraries the tool uses directly with `==` (versions verified on Kaggle); record torch, transformers and numpy as "tested with" comments, not pins | Stops future releases breaking the tool, without making installation fail on Windows/Mac where an exact torch build may not exist | Pin everything (pip freeze) or nothing |
| 71 | **(Asya)** Cross-platform: code review + fixes only; no GitHub Actions test now; README states "developed and verified on Linux (Kaggle), reviewed for Windows and Mac", real Windows/Mac test listed as future work | Keep momentum; claim only what was tested | Real test on GitHub Actions |
| 72 | Clear one-line errors for known problems (file type, missing/empty/scanned file, locked Excel, invalid key, quota, retired model) | A reviewer should know what to do next without reading a traceback | Leave Python tracebacks |
