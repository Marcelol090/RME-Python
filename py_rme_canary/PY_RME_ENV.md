# py_rme_canary Development Environment

## Context
Development of RME in Python, following `PRD.md` and `PROJECT_STRUCTURE.md`.

## Workflow Methodology (Linear & Reflective)
All agents follow a 3-Phase process: **Analysis -> Implementation -> Reflection**.
- **No Fallbacks:** Tests and Parsers fail loudly on error.
- **Strict Layering:** Core -> Logic -> Vis boundaries are absolute.

## AI Commands
- `/py-new-core`: Generate clean data structures.
- `/py-new-brush`: Port C++ brush to Python.
- `/py-parse-struct`: Helper for reading binary maps.