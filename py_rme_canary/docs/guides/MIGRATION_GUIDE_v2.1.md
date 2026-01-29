# Migration Guide v2.1: Transitioning to Quality Pipeline 2.1

## Overview
This guide covers the migration from the standalone `quality.sh` to the modular `quality-pipeline/` structure.

## Phases

### Phase 1: Environment Setup
1. Backup existing `quality.sh`.
2. Ensure Python 3.12+ is installed.
3. Install dependencies: `pip install -e quality-pipeline/`.

**Rollback:** Delete `quality-pipeline/` and restore old `quality.sh`.

### Phase 2: Configuration Override
1. Set up your environment variables:
   - `COPILOT_API_KEY`
   - `ANTIGRAVITY_API_KEY`
2. Update `quality-pipeline/config/quality.yaml` with your custom thresholds.

**Rollback:** Clear environment variables.

### Phase 3: Module Verification
1. Run `./quality-pipeline/quality.sh --dry-run` to verify all integrations.

**Rollback:** The orchestrator will automatically stop if any module fails.

## Key Features
- **Modular Shell Architecture**: Modules can be enabled/disabled independently.
- **Python Workers**: Logic is moved to Python for better testing and SDK support.
- **LLM Integration**: Dynamically generate `ast-grep` rules using Copilot or AntiGravity.
