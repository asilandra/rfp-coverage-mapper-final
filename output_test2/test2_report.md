# Test 2: unseen scenario (healthcare), live run

Extraction: 20/20 planted requirements found; 20 listed; 0 extras.

Documents written by: gemini-3.1-flash-lite · tool (extraction + judge) run by: gemini-3.5-flash-lite · different models: yes

| Metric | The tool | Keyword baseline (0.5/0.25, fixed) | Keyword baseline, best possible (0.2/0.05, tuned) |
|---|---|---|---|
| **1. Gaps caught (primary)** | 9/9 | 9/9 | 4/9 |
| 2. Status accuracy | 16/20 | 4/20 | 12/20 |
| 3. False alarms (lower is better) | 2/11 | 11/11 | 1/11 |
| 4. Slide accuracy | 18/20 | 12/20 | 15/20 |
| Keyword traps fooled (lower is better) | 1/4 | 1/4 | 4/4 |

| Planted | Matched | Expected | Tool | Expected slides | Tool slides |
|---|---|---|---|---|---|
| S1 | R01 (1.0) | Covered | ✅ Covered | [5] | [5] |
| S2 | R02 (1.0) | Partially covered | ✅ Partially covered | [6] | [6] |
| S3 | R03 (1.0) | Covered | ✅ Covered | [5] | [5] |
| S4 | R04 (1.0) | Not covered | ✅ Not covered | [] | [] |
| S5 | R06 (1.0) | Partially covered | ✅ Partially covered | [7] | [7] |
| S6 | R07 (1.0) | Covered | ❌ Partially covered | [8] | [8] |
| S7 | R05 (1.0) | Not covered | ✅ Not covered | [] | [] |
| S8 | R08 (1.0) | Covered | ✅ Covered | [9] | [9] |
| S9 | R09 (1.0) | Partially covered | ✅ Partially covered | [10] | [10] |
| D1 | R10 (1.0) | Covered | ✅ Covered | [11] | [11] |
| D2 | R11 (1.0) | Partially covered | ✅ Partially covered | [11] | [11] |
| D3 | R12 (1.0) | Covered | ✅ Covered | [11] | [11] |
| D4 | R13 (1.0) | Not covered | ❌ Partially covered | [] | [13] |
| D5 | R14 (1.0) | Covered | ✅ Covered | [12] | [12] |
| T1 | R15 (1.0) | Covered | ✅ Covered | [12] | [12] |
| T2 | R17 (1.0) | Covered | ✅ Covered | [12] | [12] |
| T3 | R16 (1.0) | Not covered | ✅ Not covered | [] | [] |
| C1 | R18 (1.0) | Partially covered | ❌ Not covered | [15] | [] |
| C2 | R19 (1.0) | Covered | ✅ Covered | [14] | [14] |
| C3 | R20 (1.0) | Covered | ❌ Partially covered | [13] | [13] |
