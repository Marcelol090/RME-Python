---
applyTo: '**'
priority: critical
type: documentation-index
lastUpdated: 2026-01-27
---

# Documentation Index - py_rme_canary

> **For AI Agents:** READ THIS FIRST in every session. This index maps ALL project documentation and provides context anchors for quick navigation. Use this to find relevant documentation before making any code changes.

Welcome to the py_rme_canary documentation! This index provides quick access to all project documentation organized by category.

---

## 🏗️ Core Documentation

### 🔎 Project Overview
- **[PRD.md](architecture/PRD.md)** - Product Requirements Document
  - Complete product vision, features, and requirements
  - Target users and success metrics
  - Technical architecture and dependencies
  - Release strategy and milestones

- **[PROJECT_STRUCTURE.md](architecture/PROJECT_STRUCTURE.md)** - Project Structure Guide
  - Ideal directory organization
  - File naming conventions
  - Module boundaries and dependency rules
  - Best practices and examples

- **[ARCHITECTURE.md](architecture/ARCHITECTURE.md)** - Architecture Guide
  - Layer overview (core/logic/vis)
  - Import patterns and dependencies
  - Common usage examples

---

## 🚦 Implementation & Status

### 📊 Status Tracking
- **[IMPLEMENTATION_STATUS.md](tracking/IMPLEMENTATION_STATUS.md)** - Feature Parity Checklist
  - Master checklist for C++ to Python porting
  - Status icons for all features
  - Parity table with percentages

- **[IMPLEMENTATION_TODO.md](tracking/IMPLEMENTATION_TODO.md)** - Actionable TODOs
  - Professional TODO tracking
  - Stub identification
  - Structure analysis



### 📋 Analysis Reports


- **[ANALISE_FALTANTE.md](analysis/ANALISE_FALTANTE.md)** - Missing Features Analysis
  - Comparative analysis with legacy C++
  - Feature-by-feature breakdown

- **[TECHNOLOGY_IMPLEMENTATION_DETAILS.md](architecture/TECHNOLOGY_IMPLEMENTATION_DETAILS.md)** - Technology Implementation Details
  - Deep-dive into implementation specifics

---

## 🛠️ Development Guides

### 🔄 Development Process
- **[WALKTHROUGH.md](guides/WALKTHROUGH.md)** - Development Walkthrough
  - Modernization phases (1-5)
  - Quality pipeline setup
  - Rollout verification

- **[CONTRIBUTING.md](guides/CONTRIBUTING.md)** - Contributing Guide
  - How to contribute code
  - Code review process
  - Development workflow

- **[TODO_EXPENSIVE.md](tracking/TODO_EXPENSIVE.md)** - Technical Debt
  - High-priority technical debt
  - Expensive refactoring tasks
  - Long-term improvement items

---

## 🛡️ Quality Assurance

### ✅ Quality Standards
- **[QUALITY_CHECKLIST.md](tracking/QUALITY_CHECKLIST.md)** - Quality Checklist
  - Quality gates and standards
  - Testing requirements
  - Code quality metrics

- **[quality_pipeline_guide.md](guides/quality_pipeline_guide.md)** - Quality Pipeline Guide
  - Pipeline architecture (v2.1)
  - Tool integration
  - Automated workflows

- **[quality_improvements_changelog.md](tracking/quality_improvements_changelog.md)** - Quality Improvements
  - History of quality improvements
  - Changelog of quality-related changes

---

## 🚀 Release & Migration

### 📦 Release Planning
- **[ROLLOUT_PLAN.md](tracking/ROLLOUT_PLAN.md)** - Rollout Plan
  - Release stages (Alpha → Beta → RC → GA)
  - Verification checklists
  - Timeline and milestones

- **[MIGRATION_GUIDE_v2.1.md](guides/MIGRATION_GUIDE_v2.1.md)** - Migration Guide
  - Migration from previous versions
  - Breaking changes
  - Upgrade instructions

- **[CHANGELOG.md](tracking/CHANGELOG.md)** - Changelog
  - Version history
  - Feature additions and bug fixes

---

## 🖥️ UI/UX & Legacy

### 🖼️ User Interface
- **[LEGACY_GUI_MAPPING.md](legacy/LEGACY_GUI_MAPPING.md)** - Legacy GUI Mapping
  - Mapping from C++ wxWidgets to PyQt6
  - UI component equivalents

- **[agents.md](guides/agents.md)** - AI Agents Documentation
  - AI agent integration
  - Automation workflows

### 📐 System Design
- **[memory_instruction.md](guides/memory_instruction.md)** - Memory System
  - Memory guard system
  - Resource limits
  - Configuration

- **[LEGACY_RME_OVERVIEW.md](legacy/LEGACY_RME_OVERVIEW.md)** - Legacy RME Overview
  - Legacy system design and mapping

---

## 🎯 Documentation by Audience

### For Product Managers
1. [PRD.md](architecture/PRD.md) - Complete product vision
2. [IMPLEMENTATION_STATUS.md](tracking/IMPLEMENTATION_STATUS.md) - Feature status
3. [ROLLOUT_PLAN.md](tracking/ROLLOUT_PLAN.md) - Release plan

### For Developers
1. [ARCHITECTURE.md](architecture/ARCHITECTURE.md) - Architecture overview
2. [PROJECT_STRUCTURE.md](architecture/PROJECT_STRUCTURE.md) - File organization
3. [CONTRIBUTING.md](guides/CONTRIBUTING.md) - How to contribute
4. [IMPLEMENTATION_TODO.md](tracking/IMPLEMENTATION_TODO.md) - What to work on

### For QA/Testers
1. [QUALITY_CHECKLIST.md](tracking/QUALITY_CHECKLIST.md) - Quality standards
2. [quality_pipeline_guide.md](guides/quality_pipeline_guide.md) - Testing pipeline
3. [WALKTHROUGH.md](guides/WALKTHROUGH.md) - Testing phases

### For Architects
1. [ARCHITECTURE.md](architecture/ARCHITECTURE.md) - System architecture
2. [PROJECT_STRUCTURE.md](architecture/PROJECT_STRUCTURE.md) - Code organization
3. [TODO_EXPENSIVE.md](tracking/TODO_EXPENSIVE.md) - Technical debt

### For Users
1. [MIGRATION_GUIDE_v2.1.md](guides/MIGRATION_GUIDE_v2.1.md) - How to migrate
2. [CHANGELOG.md](tracking/CHANGELOG.md) - What's new
3. [ROLLOUT_PLAN.md](tracking/ROLLOUT_PLAN.md) - Release timeline

---

## ⚡ Quick Start

### New to the Project?
1. Start with [PRD.md](architecture/PRD.md) to understand the product vision
2. Read [ARCHITECTURE.md](architecture/ARCHITECTURE.md) to understand the system
3. Review [PROJECT_STRUCTURE.md](architecture/PROJECT_STRUCTURE.md) for code organization
4. Check [CONTRIBUTING.md](guides/CONTRIBUTING.md) before making changes

### Want to Contribute?
1. Read [CONTRIBUTING.md](guides/CONTRIBUTING.md) for guidelines
2. Check [IMPLEMENTATION_STATUS.md](tracking/IMPLEMENTATION_STATUS.md) for what needs work
3. Review [IMPLEMENTATION_TODO.md](tracking/IMPLEMENTATION_TODO.md) for specific tasks
4. Follow [QUALITY_CHECKLIST.md](tracking/QUALITY_CHECKLIST.md) for quality standards

### Planning a Release?
1. Review [ROLLOUT_PLAN.md](tracking/ROLLOUT_PLAN.md) for release strategy
2. Check [QUALITY_CHECKLIST.md](tracking/QUALITY_CHECKLIST.md) for quality gates
3. Update [CHANGELOG.md](tracking/CHANGELOG.md) with changes
4. Follow [MIGRATION_GUIDE_v2.1.md](guides/MIGRATION_GUIDE_v2.1.md) for breaking changes

---

## 📊 Document Status

| Document | Status | Last Updated | Completeness |
|----------|--------|--------------|--------------|
| PRD.md | ✅ Current | 2026-01-14 | 100% |
| PROJECT_STRUCTURE.md | ✅ Current | 2026-01-14 | 100% |
| ARCHITECTURE.md | ✅ Current | 2025-XX-XX | 95% |
| IMPLEMENTATION_STATUS.md | ✅ Current | 2025-XX-XX | 100% |
| WALKTHROUGH.md | ✅ Current | 2026-01-11 | 100% |
| CONTRIBUTING.md | ⚠️ Needs Review | 2025-XX-XX | 80% |
| ROLLOUT_PLAN.md | ✅ Current | 2026-01-11 | 100% |
| QUALITY_CHECKLIST.md | ✅ Current | 2025-XX-XX | 95% |

---

## 🔄 Maintenance

### Document Owners
- **PRD.md:** Product Team
- **PROJECT_STRUCTURE.md:** Architecture Team
- **ARCHITECTURE.md:** Architecture Team
- **IMPLEMENTATION_STATUS.md:** Development Team
- **QUALITY_CHECKLIST.md:** QA Team

### Update Frequency
- **PRD.md:** Quarterly or on major changes
- **IMPLEMENTATION_STATUS.md:** After each feature completion
- **CHANGELOG.md:** Every release
- **ARCHITECTURE.md:** On architectural changes

---

## 📝 Contributing to Documentation

Found an issue or want to improve documentation?

1. Check if a document exists for your topic
2. Follow the document template and formatting
3. Update this index if adding new documents
4. Submit a pull request with clear description

---

## 🆘 Support

- **Issues:** [GitHub Issues](https://github.com/your-org/py_rme_canary/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-org/py_rme_canary/discussions)
- **Documentation Bugs:** Tag with `documentation` label

---
## 🤖 AI Agent Session Protocol

### Mandatory Reading Order (Every Session)

1. **First:** [README.md](README.md) (this file) - Get navigation map
2. **Second:** [memory_instruction.md](guides/memory_instruction.md) - Get current project state
3. **Third:** [agents.md](guides/agents.md) - Get coding standards and policies
4. **Context-Specific:** Refer to index above based on task

### Quick Context Lookup

| Task Type | Required Reading |
|-----------|------------------|
| **New Feature** | PRD.md → IMPLEMENTATION_STATUS.md → ARCHITECTURE.md |
| **Bug Fix** | ARCHITECTURE.md → relevant code → tests |
| **Refactoring** | PROJECT_STRUCTURE.md → TODO_EXPENSIVE.md → code |
| **Code Review** | QUALITY_CHECKLIST.md → agents.md → PR diff |
| **Documentation** | This file → CONTRIBUTING.md → specific doc |
| **Release** | ROLLOUT_PLAN.md → CHANGELOG.md → MIGRATION_GUIDE |

### Decision Protocol

**Before ANY code change:**
```
1. Read memory_instruction.md "ACTIVE WORK" section
2. Check if change aligns with current roadmap phase
3. Verify against PROJECT_STRUCTURE.md dependency rules
4. Consult PRD.md for feature requirements
5. Update memory_instruction.md if decision is significant
```

### Verification Workflow

**After implementing change:**
```bash
# 1. Quality checks
black . && isort . && mypy . --strict

# 2. Tests
pytest --cov=. --cov-report=term-missing

# 3. Security
bandit -r . -ll -i

# 4. Update docs
# - memory_instruction.md (for significant changes)
# - CHANGELOG.md (for user-facing changes)
# - IMPLEMENTATION_STATUS.md (for feature completion)
```

### Recovery Protocol (If Lost)

**If you don't know what to do:**
1. Re-read [memory_instruction.md](guides/memory_instruction.md) "ACTIVE WORK" section
2. Check [IMPLEMENTATION_TODO.md](tracking/IMPLEMENTATION_TODO.md) for next task
3. Review [agents.md](guides/agents.md) for coding standards
4. If still unclear: ASK before proceeding

**Never guess. Always verify.**

---
**Last Updated:** January 27, 2026
**Maintainer:** Documentation Team
**Version:** 1.0.1
