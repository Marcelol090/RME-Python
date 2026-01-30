---
name: Verify Parity
description: A QA protocol to certify that a Python feature matches its C++ ancestor 1:1.
---

# Skill: Verify Parity

## Context
You have implemented a feature. Now you must prove it acts exactly like the legacy RME.

## Procedure

### 1. 🕵️ Source Extraction
*   **Open C++ Source:** Read the legacy logic side-by-side.
*   **Open Python Source:** Read your implementation.

### 2. 🔬 Logic Trace (Desk Check)
*   **Conditional Check:**
    *   C++: `if (x > 10 && y < 5)`
    *   Py: `if x > 10 and y < 5:`
    *   *Verdict:* MATCH / MISMATCH
*   **Loop Check:**
    *   C++: `for (auto it = list.begin(); ...)`
    *   Py: `for item in list:`
    *   *Verdict:* MATCH / MISMATCH (Check iteration order!).

### 3. 🧪 Behavioral Test
*   **Edge Case Candidates:**
    *   What happens if input is Null?
    *   What happens at map boundaries (0, 65535)?
*   **Run Comparison:**
    *   If possible, run the scenario in the compiled RME C++ (if available) or rely on strict reading of the source code logic.

### 4. 📝 Parity Report
*   Update `IMPLEMENTATION_STATUS.md` with a "Parity Confidence" note in the Remarks column.
    *   Example: "Logic Verified (C++ `doodad_brush.cpp` L10-50 mapped to `doodad.py` L40-80)."

## Definition of Done
1.  [ ] Logic flow manually traced against C++.
2.  [ ] Edge cases identified and tested in `pytest`.
3.  [ ] `IMPLEMENTATION_STATUS.md` updated with verification note.
