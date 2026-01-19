---
applyTo: '**'
priority: critical
type: quick-reference
lastUpdated: 2026-01-18
---

# Quick Reference Guide
## py_rme_canary - Agent Decision Tree & Workflows

**Purpose:** 1-page decision tree for routing tasks to correct agent  
**Use When:** Starting any new task or unsure which agent to use

---

## 🎯 **AGENT SELECTION (START HERE)**

```
┌──────────────────────────────────────────────────────┐
│ What type of task do you have?                      │
└──────────────────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┬──────────────┐
         │           │           │              │
    ┌────▼────┐ ┌───▼────┐ ┌────▼─────┐ ┌─────▼──────┐
    │  LIVE   │ │  FAST  │ │   DEEP   │ │   REVIEW   │
    │ CODING  │ │  FIX   │ │  DESIGN  │ │   CODE     │
    └────┬────┘ └───┬────┘ └────┬─────┘ └─────┬──────┘
         │          │            │             │
         ▼          ▼            ▼             ▼
  ANTIGRAVITY    SONNET        OPUS         HAIKU
  (autocomplete) (executor)  (architect)   (reviewer)
```

---

## 📋 **DECISION TREE**

### **Question 1: Is this real-time coding assistance?**

```yaml
YES (Autocomplete, inline fixes, live suggestions):
  agent: ANTIGRAVITY
  examples:
    - "Complete this import statement"
    - "Add missing type hints as I type"
    - "Fix this layer violation inline"
    - "Suggest function signature based on context"
  
  ↓ Go to: ANTIGRAVITY Workflow (Section A)
```

### **Question 2: Is this a simple, well-defined task?**

```yaml
Criteria:
  - < 500 LOC to change
  - < 3 files affected
  - Requirements are crystal clear
  - No architectural decisions needed

YES:
  agent: SONNET
  examples:
    - "Fix bug in GroundBrush.apply()"
    - "Add type hints to otbm_loader.py"
    - "Refactor parse_tile() to reduce complexity"
    - "Implement test for DoorBrush edge case"
  
  ↓ Go to: SONNET Workflow (Section B)

NO (>500 LOC OR unclear requirements OR architecture change):
  agent: OPUS
  ↓ Go to: Question 3
```

### **Question 3: What type of complex task?**

```yaml
New Feature (>500 LOC):
  agent: OPUS (design) → SONNET (implement)
  examples:
    - "Implement full Door Brush feature"
    - "Add Properties Panel to UI"
    - "Create PNG export functionality"
  
  ↓ Go to: OPUS Workflow - New Feature (Section C1)

Architecture Change:
  agent: OPUS (design) → SONNET (migrate)
  examples:
    - "Refactor OTBM loader into modules"
    - "Migrate to new project structure"
    - "Redesign rendering pipeline"
  
  ↓ Go to: OPUS Workflow - Architecture (Section C2)

Breaking Change:
  agent: OPUS (plan) → SONNET (implement)
  examples:
    - "Change OTBM save format (v2 → v3)"
    - "Modify GameMap API (add async support)"
    - "Refactor brush protocol (incompatible)"
  
  ↓ Go to: OPUS Workflow - Breaking Change (Section C3)
```

---

## 🚀 **SECTION A: ANTIGRAVITY WORKFLOW**

**Use For:** Real-time coding assistance (autocomplete, inline fixes)

```yaml
Step 1: Enable AntiGravity
  command: "antigravity --enable --project py_rme_canary"
  
Step 2: Start Coding
  action: "Type normally in your IDE"
  
Step 3: Accept Suggestions
  - TAB: Accept autocomplete
  - ESC: Dismiss suggestion
  - Ctrl+.: Quick fix error
  
Step 4: Monitor Performance
  latency: "< 300ms per suggestion"
  acceptance_rate: "> 60%"
```

**When to Escalate:**
- Suggestion requires >100 LOC
- Architectural decision needed
- Uncertainty about approach

→ Escalate to SONNET or OPUS

---

## ⚡ **SECTION B: SONNET WORKFLOW**

**Use For:** Fast execution (<500 LOC, <3 files, clear requirements)

### **Workflow Steps**

```yaml
1. VERIFY SCOPE (30 seconds)
   checklist:
     - [ ] < 500 LOC?
     - [ ] < 3 files?
     - [ ] Requirements clear?
     - [ ] No architecture decisions?
   
   if ANY no: ESCALATE TO OPUS

2. LOAD CONTEXT (1 minute)
   read_in_order:
     - docs/memory_instruction.md (ACTIVE WORK section)
     - docs/PROJECT_STRUCTURE.md (file location rules)
     - Relevant source files
     - Existing tests
   
3. IMPLEMENT (TDD) (3 minutes)
   process:
     - Write failing test FIRST
     - Implement minimal code to pass
     - Refactor (if needed)
     - Add type hints + docstrings
   
4. VALIDATE (1 minute)
   run_all:
     - black . && isort .
     - mypy . --strict
     - pytest --cov --cov-fail-under=90
     - bandit -r . -ll
   
   if ANY fail: FIX before proceeding

5. COMPLETE
   response_format:
     - Summary of changes
     - Files modified (with +/- counts)
     - Validation results
     - Next action (explicit command)
```

### **Example Timeline**

```
00:00 - Task received: "Fix bug in GroundBrush"
00:30 - Scope verified: ✅ <100 LOC, 1 file, clear
01:30 - Context loaded + test written
04:30 - Implementation complete
05:30 - Validation passed
06:00 - Task complete ✅

Total: 6 minutes
```

---

## 🧠 **SECTION C1: OPUS WORKFLOW - NEW FEATURE**

**Use For:** Complex features (>500 LOC, multi-component)

### **7-Phase DEEP Framework**

```yaml
1. DISCOVER (30 min)
   output: "Problem Statement"
   questions:
     - What is user trying to achieve?
     - What are edge cases?
     - What are success criteria?
   
2. EXPLORE (1 hour)
   output: "Research Report"
   tasks:
     - Analyze C++ implementation
     - Research Python equivalents
     - Check existing code
   
3. ENGINEER (2 hours)
   output: "Design Specification"
   deliverables:
     - Architecture diagram
     - Component design
     - API surface
     - Performance estimates
   
4. ELABORATE (1 hour)
   output: "Milestone Plan"
   requirements:
     - Each milestone < 300 LOC
     - Clear dependencies
     - Time estimates
   
5. PROTOTYPE (2 hours)
   output: "Prototype Validation"
   goal:
     - Validate core algorithm
     - Test performance
     - Confirm approach works
   
6. PLAN (30 min)
   output: "Sonnet Handoff Document"
   includes:
     - Crystal-clear instructions
     - Code templates
     - Acceptance criteria
   
7. DELEGATE → SONNET
   action: "Assign milestones sequentially"
   
8. EVALUATE (after implementation)
   output: "Post-Implementation Report"
   review:
     - Metrics vs targets
     - Lessons learned
     - Recommendations
```

### **Example Timeline**

```
Day 1 (Opus):
  09:00-09:30 - DISCOVER
  09:30-10:30 - EXPLORE
  10:30-12:30 - ENGINEER
  13:30-14:30 - ELABORATE
  14:30-16:30 - PROTOTYPE
  16:30-17:00 - PLAN
  
Day 2-3 (Sonnet):
  M1: 2 hours
  M2: 4 hours
  M3: 2 hours
  
Day 4 (Opus):
  09:00-10:00 - EVALUATE

Total: ~4 days (1 day design + 2 days implementation + 1 day review)
```

---

## 🏗️ **SECTION C2: OPUS WORKFLOW - ARCHITECTURE**

**Use For:** Refactoring, module creation, layer changes

### **Architecture Change Protocol**

```yaml
1. IMPACT ANALYSIS (1 hour)
   assess:
     - How many files affected?
     - Breaking changes?
     - Migration path?
   
2. DESIGN NEW STRUCTURE (2 hours)
   create:
     - New directory structure
     - Dependency graph
     - Migration plan
   
3. MIGRATION PLAN (2 hours)
   strategy: "Strangler Fig Pattern"
   phases:
     - Phase 1: Create new structure (coexist)
     - Phase 2: Migrate incrementally
     - Phase 3: Deprecate old
     - Phase 4: Remove deprecated
   
4. MILESTONE BREAKDOWN (1 hour)
   requirements:
     - Each milestone independently testable
     - Can rollback at any milestone
     - < 300 LOC per milestone
   
5. DELEGATE → SONNET
   assign: "Milestones 1 by 1"
   
6. VALIDATE ARCHITECTURE (after each milestone)
   checks:
     - No circular dependencies (pydeps)
     - Layer compliance
     - Tests pass
```

---

## ⚠️ **SECTION C3: OPUS WORKFLOW - BREAKING CHANGE**

**Use For:** API changes, data format changes, incompatible updates

### **Breaking Change Protocol**

```yaml
1. ASSESS IMPACT (30 min)
   identify:
     - What breaks?
     - Who is affected? (users, other modules)
     - Can it be avoided?
   
2. DESIGN MIGRATION (1 hour)
   create:
     - Backward compatibility layer (if possible)
     - Migration script
     - Rollback plan
   
3. COMMUNICATION PLAN (30 min)
   prepare:
     - Changelog entry
     - Migration guide
     - Deprecation warnings
   
4. IMPLEMENT WITH DEPRECATION (varies)
   pattern:
     - Release N: Add new API (old still works)
     - Release N+1: Deprecate old API (warnings)
     - Release N+2: Remove old API
   
5. VALIDATE MIGRATION (1 hour)
   test:
     - Old code still works (with warnings)
     - New code works
     - Migration script works
```

---

## 🚨 **ESCALATION TRIGGERS**

### **AntiGravity → Sonnet**

```yaml
when:
  - Suggestion requires >100 LOC
  - File has >5 type errors
  - User writes "# TODO: implement X"

action: "Open Sonnet task panel"
```

### **Sonnet → Opus**

```yaml
when:
  - > 500 LOC to change
  - > 3 files to modify
  - Requirements unclear
  - Architecture decision needed
  - Breaking change

action: "Create escalation report (see template below)"
```

### **Escalation Report Template**

```markdown
🚨 ESCALATING TO OPUS

**Task:** [Original request]

**Trigger:**
- [ ] > 500 LOC
- [ ] > 3 files
- [ ] Unclear requirements
- [ ] Architecture decision
- [ ] Breaking change

**Context Provided:**
- Current state: [Analysis done]
- Attempted approaches: [If any]
- Blockers: [What's blocking]

**Request:**
Opus, please provide:
1. [Specific need 1]
2. [Specific need 2]
```

---

## ✅ **VALIDATION COMMANDS**

Copy-paste these for quick validation:

```bash
# Full quality gates (all agents)
black . && isort . && mypy . --strict && pytest --cov --cov-fail-under=90 && bandit -r . -ll

# Just formatting
black . && isort .

# Just type check
mypy . --strict --show-error-codes

# Just tests
pytest --cov --cov-fail-under=90 -v

# Just security
bandit -r . -ll

# Check circular dependencies
pydeps py_rme_canary --show-cycles

# Check layer violations (in core/)
grep -r "from.*vis_layer\|from.*logic_layer" py_rme_canary/core/
```

---

## 📊 **QUICK METRICS**

### **Agent Performance Targets**

| Agent | Task Time | Files | LOC | Quality Gates |
|-------|-----------|-------|-----|---------------|
| **AntiGravity** | <300ms | 1 | N/A | Inline checks |
| **Sonnet** | 3-5 min | 1-3 | <500 | 100% pass |
| **Opus (Design)** | 4-8 hours | N/A | N/A | Architecture valid |
| **Opus (Full)** | 2-4 days | N/A | >500 | 100% pass |

### **Success Criteria**

```yaml
sonnet:
  - Speed: > 80% of tasks in < 5 min
  - Quality: > 95% pass rate (first try)
  - Escalation: < 10% of tasks

opus:
  - Accuracy: > 90% milestone estimates (within 20%)
  - Rework: Zero architectural rework
  - Delegation: > 90% Sonnet completion (no re-escalation)

antigravity:
  - Latency: > 95% suggestions < 300ms
  - Acceptance: > 60% acceptance rate
  - Accuracy: < 5% false positives
```

---

## 🎯 **DECISION FLOWCHART (ASCII)**

```
START
  │
  ▼
Is it real-time coding?
  ├─YES─→ ANTIGRAVITY (autocomplete/inline fixes)
  │
  └─NO
      │
      ▼
  Is it simple? (<500 LOC, <3 files, clear)
      ├─YES─→ SONNET (execute)
      │           │
      │           ▼
      │       TDD → Implement → Validate → Done
      │
      └─NO
          │
          ▼
      Is it complex?
          ├─New Feature─→ OPUS (design) → SONNET (implement)
          │                   │
          │                   └─→ DEEP (7 phases) → Delegate
          │
          ├─Architecture─→ OPUS (design) → SONNET (migrate)
          │                   │
          │                   └─→ Strangler Fig → Delegate
          │
          └─Breaking Change─→ OPUS (plan) → SONNET (implement)
                              │
                              └─→ Migration Plan → Delegate
```

---

## 🔄 **VERSION HISTORY**

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-18 | Initial quick reference |

---

**END OF DOCUMENT**

**Print this page and keep at your desk for instant reference!**
