<!--
Sync Impact Report:
- Version change: Initial creation → 1.0.0
- Modified principles: N/A (initial constitution)
- Added sections: All sections (initial creation)
  - Core Principles: Library-First, CLI Interface, Test-First, Integration Testing, Simplicity
  - Development Workflow
  - Governance
- Removed sections: N/A
- Templates requiring updates:
  ✅ plan-template.md - Constitution Check section references validated
  ✅ spec-template.md - Requirements alignment validated
  ✅ tasks-template.md - Task categorization validated
  ✅ Command files - Agent references validated (generic guidance maintained)
- Follow-up TODOs: None
-->

# AlphaAgent Constitution

## Core Principles

### I. Library-First

Every feature MUST start as a standalone library. Libraries MUST be self-contained, independently testable, and fully documented. Each library MUST have a clear, singular purpose—no organizational-only libraries without functional value.

**Rationale**: Modular design enables independent testing, reuse across contexts, and clear ownership boundaries. Libraries force explicit interfaces and reduce coupling.

### II. CLI Interface

Every library MUST expose its functionality via a command-line interface. The CLI MUST follow a text in/out protocol: input via stdin or arguments, output to stdout, errors to stderr. The CLI MUST support both JSON and human-readable output formats.

**Rationale**: CLI interfaces ensure debuggability through text I/O, enable shell scripting integration, and provide a universal interface pattern. Text protocols are inspectable, testable, and composable.

### III. Test-First (NON-NEGOTIABLE)

Test-driven development is MANDATORY for all features. The workflow MUST be: tests written → user approved → tests fail → implementation begins. The Red-Green-Refactor cycle MUST be strictly enforced without exception.

**Rationale**: Test-first development ensures requirements are understood before implementation, prevents scope creep, and creates living documentation. Pre-approved failing tests eliminate ambiguity about expected behavior.

### IV. Integration Testing

Integration tests are REQUIRED for:
- New library contract tests (verify public interfaces)
- Contract changes (ensure backward compatibility)
- Inter-service communication (validate integration points)
- Shared schemas (ensure data contract compliance)

**Rationale**: Unit tests verify components in isolation but cannot catch integration failures. Contract tests document and enforce interface agreements. Integration tests catch real-world failures before production.

### V. Simplicity

Start simple and follow YAGNI (You Aren't Gonna Need It) principles. Add complexity ONLY when requirements demand it, and every added complexity MUST be justified in writing. Prefer straightforward solutions over clever ones.

**Rationale**: Complexity is the enemy of maintainability. Simple code is easier to understand, test, debug, and modify. Premature optimization and over-engineering create technical debt without proven value.

## Development Workflow

### Feature Specification

All features MUST begin with a specification document (`spec.md`) that describes WHAT the feature does and WHY it's needed, without specifying HOW to implement it. Specifications MUST:

- Focus on user scenarios and acceptance criteria
- Define measurable success criteria
- Identify functional requirements
- Remain technology-agnostic (no implementation details)

### Implementation Planning

After specification approval, an implementation plan (`plan.md`) MUST be created that includes:

- Technical context and technology choices with rationale
- Constitution compliance check
- Project structure decisions
- Research findings for unclear aspects
- Data models and API contracts
- Complexity justifications (if any violations exist)

### Task Breakdown

Implementation plans MUST be broken down into actionable tasks (`tasks.md`) that:

- Map to specific user stories
- Include exact file paths
- Mark parallel execution opportunities
- Specify dependencies explicitly
- Enable independent testing of each user story

### Quality Gates

Before proceeding to implementation, ALL of the following MUST be complete:

1. Specification approved and free of [NEEDS CLARIFICATION] markers
2. Implementation plan passes Constitution Check
3. Tests written, approved, and confirmed to fail
4. Tasks broken down with clear file paths and dependencies

## Governance

This constitution supersedes all other development practices and guidelines. Any deviation from these principles MUST be documented with:

- Specific principle violated
- Justification for the violation
- Explanation of why simpler alternatives were rejected
- Approval from project stakeholders

### Amendment Process

Constitution amendments require:
1. Written proposal documenting the change and rationale
2. Review of impact on existing templates and workflows
3. Migration plan for existing features (if applicable)
4. Approval before adoption
5. Version bump according to semantic versioning

### Versioning Policy

- **MAJOR**: Backward incompatible governance changes or principle removals/redefinitions
- **MINOR**: New principles added or material expansion of existing guidance
- **PATCH**: Clarifications, wording improvements, non-semantic refinements

### Compliance Review

All pull requests and code reviews MUST verify compliance with this constitution. Reviewers MUST:

- Check for unjustified complexity
- Verify test-first workflow was followed
- Validate library and CLI interface requirements
- Confirm integration test coverage for contracts
- Ensure simplicity principles were applied

**Version**: 1.0.0 | **Ratified**: 2026-01-30 | **Last Amended**: 2026-01-30
