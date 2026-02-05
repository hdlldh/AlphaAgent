# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [single/web/mobile - determines source structure]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on the AlphaAgent Constitution (v1.0.0), verify compliance with these principles:

### I. Library-First
- [ ] Feature designed as standalone library
- [ ] Library is self-contained and independently testable
- [ ] Library has clear, singular purpose
- [ ] Library has complete documentation plan

**Violations**: [List any violations or mark "None"]
**Justification**: [Required if violations exist - explain why needed and why simpler alternatives rejected]

### II. CLI Interface
- [ ] Library exposes functionality via CLI
- [ ] Text in/out protocol: stdin/args → stdout, errors → stderr
- [ ] Supports both JSON and human-readable output

**Violations**: [List any violations or mark "None"]
**Justification**: [Required if violations exist]

### III. Test-First (NON-NEGOTIABLE)
- [ ] Tests will be written before implementation
- [ ] Tests will be approved by user before implementation
- [ ] Tests will fail before implementation begins
- [ ] Red-Green-Refactor cycle documented in tasks

**Violations**: [List any violations or mark "None"]
**Justification**: [This principle is NON-NEGOTIABLE - violations require escalation]

### IV. Integration Testing
- [ ] Contract tests planned for public interfaces
- [ ] Integration tests planned for external dependencies
- [ ] Contract changes have backward compatibility tests
- [ ] Shared schemas have validation tests

**Violations**: [List any violations or mark "None"]
**Justification**: [Required if violations exist]

### V. Simplicity
- [ ] Solution uses simplest approach that meets requirements
- [ ] No premature optimization
- [ ] No unnecessary abstraction layers
- [ ] Complexity is justified in Complexity Tracking table

**Violations**: [List any violations or mark "None"]
**Justification**: [Required if violations exist]

**Overall Status**: [PASS / FAIL - if FAIL, must resolve before Phase 0]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
