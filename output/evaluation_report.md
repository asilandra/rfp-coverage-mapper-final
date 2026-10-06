# Evaluation report: coverage judging

Scored on the 18 planted requirements (answer key written before the documents existed). Judge model for all requirements: **gemini-3.5-flash-lite**.

| Metric | The tool | Keyword baseline (pre-registered thresholds 0.5/0.25) | Keyword baseline, best possible (tuned on the answers: 0.3/0.25) |
|---|---|---|---|
| **1. Gaps caught (primary)** | **8/8** | 8/8 | 6/8 |
| 2. Status accuracy | 16/18 | 6/18 | 12/18 |
| 3. False alarms (lower is better) | 2/10 | 10/10 | 3/10 |
| 4. Slide accuracy | 18/18 | 12/18 | 12/18 |
| Keyword traps fooled by (lower is better) | 0/5 | 1/5 | 1/5 |

**How to read this:** gap detection is the primary metric, but it must be read together with false alarms: a method that flags everything as a gap also "catches" every gap. The baseline's best-possible column is optimistic on purpose (its thresholds were tuned on the answer key); the tool's prompt was not tuned.

## Requirement by requirement (planted answer vs tool vs baseline)

| Planted | Expected | Tool | Baseline | Expected slides | Tool slides | Baseline slides |
|---|---|---|---|---|---|---|
| S1 | Covered | ✅ Covered | ❌ Partially covered | [5] | [5] | [5] |
| S2 | Covered | ✅ Covered | ❌ Not covered | [6] | [6] | [] |
| S3 | Partially covered | ✅ Partially covered | ✅ Partially covered | [5] | [5, 11] | [5] |
| S4 | Not covered | ✅ Not covered | ❌ Partially covered | [] | [] | [13] |
| S5 | Covered | ✅ Covered | ❌ Partially covered | [7] | [7] | [7, 11] |
| S6 | Not covered | ✅ Not covered | ✅ Not covered | [] | [] | [] |
| S7 | Partially covered | ✅ Partially covered | ❌ Not covered | [9] | [9] | [] |
| S8 | Covered | ✅ Covered | ❌ Partially covered | [8] | [8] | [14] |
| D1 | Covered | ❌ Partially covered | ❌ Partially covered | [10] | [5, 10] | [10] |
| D2 | Covered | ✅ Covered | ❌ Partially covered | [10] | [6, 10] | [14] |
| D3 | Partially covered | ✅ Partially covered | ✅ Partially covered | [7] | [7, 11] | [7, 11] |
| D4 | Covered | ✅ Covered | ❌ Partially covered | [10] | [10] | [10] |
| D5 | Not covered | ✅ Not covered | ✅ Not covered | [] | [] | [] |
| T1 | Covered | ✅ Covered | ❌ Partially covered | [11] | [11] | [11] |
| T2 | Covered | ❌ Partially covered | ❌ Not covered | [11] | [11] | [] |
| T3 | Not covered | ✅ Not covered | ✅ Not covered | [] | [] | [] |
| C1 | Partially covered | ✅ Partially covered | ✅ Partially covered | [12] | [12] | [12] |
| C2 | Covered | ✅ Covered | ❌ Partially covered | [13] | [13] | [13] |
