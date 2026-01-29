# Phase 5: Rollout & Verification Plan

## 1. Release Stages

### Alpha (Internal Testing)
**Target:** Development team only
**Duration:** 2 weeks
**Criteria:**
- [ ] Phase 1 & 2 complete (Quality Gates + Rendering)
- [ ] All unit tests passing (>80% coverage)

**Deliverables:**
- Internal build with debug logging enabled
- Performance baseline document
- Known issues list

---

### Beta (Selected Users)
**Target:** 10-20 power users from community
**Duration:** 4 weeks
**Criteria:**
- [ ] Phase 3 & 4 complete (UI/UX + Logic Parity)
- [ ] Smoke test checklist passed
- [ ] Documentation draft ready

**Deliverables:**
- Beta installer/package
- Feedback collection form
- Migration guide for users

---

### Release Candidate (RC)
**Target:** All users who opt-in
**Duration:** 2 weeks
**Criteria:**
- [ ] All Beta feedback addressed
- [ ] Performance within 10% of legacy
- [ ] No P0/P1 bugs open

**Deliverables:**
- RC build with telemetry (opt-in)
- Final documentation
- Rollback instructions

---

### General Availability (GA)
**Target:** All users
**Criteria:**
- [ ] RC testing complete
- [ ] All unit tests passing (>80% coverage)
- [ ] Localization reviewed
- [ ] Changelog finalized

---

## 2. Verification Checklists

### 2.1 Automated Testing

```bash
# Run full test suite
./quality-pipeline/quality.sh --apply --verbose
./quality-pipeline/quality.sh --verify
./quality-pipeline/quality.sh --refactor
./quality-pipeline/quality.sh --qa
./quality-pipeline/quality.sh --scripts
./quality-pipeline/quality.sh --dev

# Specific test categories
pytest tests/unit -v --cov=py_rme_canary
pytest tests/ui -v --qt-no-window-capture
pytest tests/integration -v

# Performance benchmarks
pytest tests/performance --benchmark-only
```

### 2.2 Automated Smoke Test

| # | Workflow | Steps | Expected Result |
|---|----------|-------|-----------------|
| 1 | **Open Map** | File > Open > Select .otbm | Map loads, viewport shows content |
| 2 | **Select Brush** | Click Ground brush in palette | Brush highlighted, cursor changes |
| 3 | **Draw Tiles** | Click and drag on canvas | Tiles painted, preview shown |
| 4 | **Undo** | Ctrl+Z | Tiles reverted to previous state |
| 5 | **Redo** | Ctrl+Y | Tiles restored |
| 6 | **Save Map** | File > Save | File updated, no data loss |
| 7 | **Selection** | Shift+drag box | Area selected, can copy/cut |
| 8 | **Zoom** | Scroll wheel | Canvas zooms in/out smoothly |
| 9 | **Pan** | Right-click drag | Canvas pans correctly |
| 10 | **Search** | Type in search box | Results filter in real-time |
| 11 | **Find Item** | Type in search box | Results filter in real-time |
| 12 | **Find Creature** | Type in search box | Results filter in real-time |
| 13 | **Find House** | Type in search box | Results filter in real-time |
| 14 | **Find Npc** | Type in search box | Results filter in real-time |
| 15 | **Find Monster** | Type in search box | Results filter in real-time |
| 16 | **Find Spawn** | Type in search box | Results filter in real-time |
| 17 | **Find Spawn** | Type in search box | Results filter in real-time |

### 2.3 Performance Test Script

```python
# tests/performance/test_benchmarks.py
import pytest
from py_rme_canary.core.io import load_otbm
from py_rme_canary.vis_layer.renderer import RenderFrame

@pytest.mark.benchmark
def test_map_load_time(benchmark):
    """Map loading should complete in <2 seconds."""
    result = benchmark(load_otbm, "tests/fixtures/test_map_1024x1024.otbm")
    assert benchmark.stats["mean"] < 2.0

@pytest.mark.benchmark
def test_render_frame_time(benchmark):
    """Single frame render should be <16ms (60 FPS)."""
    frame = RenderFrame()
    result = benchmark(frame.render)
    assert benchmark.stats["mean"] < 0.016
```

---

## 3. Rollback Strategy

### If Critical Bug Found in Production:

1. **Communicate:** Post status to community channels
2. **Rollback:**
   ```bash
   git revert HEAD~N  # Revert last N commits
   # OR
   git checkout v1.x.x  # Checkout last stable tag
   ```
3. **Hotfix:** Create `hotfix/` branch, fix issue
4. **Verify:** Run full CI pipeline on hotfix
5. **Deploy:** Merge and release patch version

### Feature Flags (Recommended)

```python
# config/feature_flags.py
FEATURE_FLAGS = {
    "opengl_renderer": False,  # Toggle new renderer
    "new_theme_system": True,  # New UI styling
    "ai_integration": False,   # LLM features (v2.1+)
}
```

---

## 4. Documentation Checklist

- [ ] README.md updated with new features
- [ ] CHANGELOG.md with all changes since last release
- [ ] missing_implementation.md updated with new features
- [ ] API documentation (if applicable)
- [ ] User guide / wiki updates
- [ ] Migration guide (if breaking changes)
- [ ] Video tutorial (optional)

---

## 5. Post-Release Monitoring

### Metrics to Track:
- Crash rate (target: <0.1%)
- Performance regressions
- User feedback sentiment
- Feature adoption rate

### Tools:
- Telemetry dashboard (if enabled)
- GitHub Issues tracking
- Community Discord/Forum

---

## 6. Timeline Summary

| Phase | Duration | Start Date | End Date |
|-------|----------|------------|----------|
| Alpha | 2 weeks | TBD | TBD |
| Beta | 4 weeks | TBD | TBD |
| RC | 2 weeks | TBD | TBD |
| GA | - | TBD | - |

---

**Document Version:** 1.0.0
**Last Updated:** 2026-01-11
