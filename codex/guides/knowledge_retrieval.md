# Knowledge Retrieval Guide (File Search)

(Concept source: OpenAI File Search Tool)

## Philosophy
In `py_rme_canary`, "File Search" isn't just about reading files—it's about effectively retrieving the *legacy logic* required for 1:1 parity and finding the *Python references* needed for implementation.

## 1. Vector Search Simulation
Since you don't have a semantic vector store, use `grep_search` and `find_by_name` as your retrieval mechanisms.

### Strategy: "Concept to Code"
When implementing a feature (e.g., "Carpet Brush"), do not guess. Search for the concept in the legacy codebase:
1.  **Keyword Search:** `grep_search("CarpetBrush", "RME/source")`
2.  **Implementation Retrieval:** Read the found files (`carpet_brush.cpp`, `carpet_brush.h`).
3.  **Cross-Reference:** Search for the legacy references in the new codebase (`py_rme_canary`) to see if stubs exist.

## 2. Context Management
*   **Chunking:** Do not read entire 5000-line C++ files. Read the specific functions (`draw`, `undraw`) relevant to your task.
*   **Vector Store Update:** treating `IMPLEMENTATION_STATUS.md` as your index. If you create a new file, add it there so future agents "find" it.

## 3. Metadata Filtering
*   Filter by **Extension:** When looking for logic, filter for `.cpp`/`.h` (Legacy) or `.py` (New).
*   Filter by **Directory:** Limit scope to `logic_layer` when working on business rules.

## 4. External Documentation (The Web)
*   **Trigger:** If a task involves a third-party library (PyQt6, Pytest, OpenAI) or an API.
*   **Action:**
    1.  `search_web(query)` to find the official docs.
    2.  `fetch_webpage(url)` to read the specific version details.
    3.  **Cross-Check:** Compare the fetched info with your training data. The fetched info WINS.
