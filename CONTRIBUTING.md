# Contributing to AlphaAgent

Thank you for your interest in contributing to AlphaAgent! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Constitution](#project-constitution)
- [Development Workflow](#development-workflow)
- [Testing Guidelines](#testing-guidelines)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Commit Message Guidelines](#commit-message-guidelines)

## Code of Conduct

This project follows standard open-source conduct principles:
- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Prioritize project goals over personal preferences

## Getting Started

Before contributing:
1. Read the [README.md](README.md) to understand the project
2. Review the [Project Constitution](.specify/memory/constitution.md)
3. Check [existing issues](../../issues) for tasks to work on
4. Join discussions to understand current priorities

## Development Setup

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git for version control
- Telegram account (for bot testing)
- API key for LLM provider (Anthropic, OpenAI, or Gemini)

### Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd AlphaAgent

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -e ".[dev]"

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# At minimum, set:
#   - ANTHROPIC_API_KEY (or OPENAI_API_KEY/GEMINI_API_KEY)
#   - STOCK_ANALYZER_TELEGRAM_TOKEN

# Initialize database
python -m stock_analyzer.cli init-db

# Run tests to verify setup
uv run pytest
```

## Project Constitution

AlphaAgent follows strict development principles outlined in the [Constitution](.specify/memory/constitution.md):

### 1. Test-First (NON-NEGOTIABLE)

**Red-Green-Refactor workflow is mandatory:**

```bash
# 1. RED: Write failing tests first
uv run pytest tests/unit/test_new_feature.py  # Should FAIL

# 2. GREEN: Implement minimum code to pass
# ... write implementation ...
uv run pytest tests/unit/test_new_feature.py  # Should PASS

# 3. REFACTOR: Improve code quality
# ... refactor while keeping tests green ...
```

**Rules:**
- NEVER skip writing tests first
- NEVER commit code without tests
- NEVER merge PRs with failing tests
- Tests must fail before implementation (verify Red phase)

### 2. Library-First

- Core functionality in `src/stock_analyzer/` as standalone library
- CLI in `src/stock_analyzer/cli.py` as thin wrapper
- Scripts in `src/scripts/` for workflows
- No business logic in CLI/scripts

### 3. CLI Interface

- Text input/output protocol
- JSON support via `--json` flag
- Exit codes: 0 (success), 1 (error), 130 (interrupted)
- Chainable commands via pipes

### 4. Integration Testing

- Contract tests for external APIs (mocked)
- Integration tests for workflows (end-to-end)
- Unit tests for isolated components
- All three types required for new features

### 5. Simplicity

- No premature optimization
- YAGNI (You Aren't Gonna Need It)
- Favor readability over cleverness
- Delete code aggressively

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Follow TDD Workflow

For each new feature or bug fix:

```bash
# Write tests FIRST (they should fail)
# Edit tests/unit/test_your_feature.py
uv run pytest tests/unit/test_your_feature.py -v

# Implement feature (make tests pass)
# Edit src/stock_analyzer/your_feature.py
uv run pytest tests/unit/test_your_feature.py -v

# Refactor if needed (tests should stay green)
uv run pytest tests/unit/test_your_feature.py -v

# Run full test suite
uv run pytest
```

### 3. Maintain Code Quality

```bash
# Check test coverage (aim for >80%)
uv run pytest --cov=stock_analyzer --cov-report=term-missing

# Format code (if formatters installed)
black src/ tests/
isort src/ tests/

# Type check (if mypy installed)
mypy src/
```

### 4. Commit Changes

```bash
# Stage specific files (avoid git add .)
git add src/stock_analyzer/your_feature.py
git add tests/unit/test_your_feature.py

# Commit with descriptive message
git commit -m "Add feature: your feature description"
```

## Testing Guidelines

### Test Organization

```
tests/
├── contract/       # External API contract tests (mocked)
├── integration/    # End-to-end workflow tests
└── unit/          # Isolated component tests
```

### Test Markers

Use pytest markers to organize tests:

```python
@pytest.mark.US1  # User Story 1
@pytest.mark.asyncio  # Async test
@pytest.mark.slow  # Long-running test
```

### Writing Tests

**Good test example:**

```python
def test_analyze_stock_success(self, mock_stock_data):
    """Test successful stock analysis."""
    # Arrange
    analyzer = Analyzer(llm_client, fetcher, storage)

    # Act
    result = await analyzer.analyze_stock("AAPL")

    # Assert
    assert result.stock_symbol == "AAPL"
    assert result.confidence_level in ["high", "medium", "low"]
    assert len(result.risk_factors) > 0
```

**Test principles:**
- One assertion concept per test
- Descriptive test names (what, when, expected)
- Arrange-Act-Assert pattern
- Mock external dependencies
- Test edge cases and error paths

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_analyzer.py

# Run tests matching pattern
uv run pytest -k "test_analyze"

# Run with coverage
uv run pytest --cov=stock_analyzer --cov-report=html

# Run specific user story tests
uv run pytest -k US1  # User Story 1 only
```

## Code Style

### Python Style

- Follow PEP 8
- Use type hints where beneficial
- Maximum line length: 100 characters
- Use double quotes for strings
- Prefer f-strings for formatting

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Methods**: `snake_case()`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

### Documentation

Use Google-style docstrings:

```python
def analyze_stock(symbol: str, force: bool = False) -> Insight:
    """
    Analyze a single stock and generate insights.

    Args:
        symbol: Stock ticker symbol (e.g., "AAPL")
        force: If True, re-analyze even if exists for today

    Returns:
        Insight object with analysis results

    Raises:
        InvalidSymbolError: If symbol is invalid
        AnalysisError: If LLM analysis fails
    """
    pass
```

### Import Organization

```python
# Standard library
import json
import sys
from datetime import date

# Third-party
import pytest
from telegram import Update

# Local
from stock_analyzer.config import Config
from stock_analyzer.models import Insight
```

## Pull Request Process

### Before Submitting

1. **Ensure tests pass:**
   ```bash
   uv run pytest
   ```

2. **Check coverage:**
   ```bash
   uv run pytest --cov=stock_analyzer --cov-report=term-missing
   ```

3. **Update documentation:**
   - Add/update docstrings
   - Update README.md if needed
   - Update CHANGELOG if present

4. **Verify no secrets committed:**
   ```bash
   git diff --staged
   ```

### PR Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing
- [ ] Coverage maintained/improved

## Checklist
- [ ] Followed TDD workflow (Red-Green-Refactor)
- [ ] Code follows project style guidelines
- [ ] Docstrings added/updated
- [ ] No secrets or sensitive data committed
- [ ] README updated (if needed)

## Related Issues
Closes #<issue-number>
```

### Review Process

1. **Automated Checks**:
   - CI tests must pass
   - Coverage threshold must be met (>70%)
   - No merge conflicts

2. **Code Review**:
   - At least one approving review required
   - Address all review comments
   - Squash commits if needed

3. **Merge**:
   - Use "Squash and merge" for clean history
   - Delete branch after merge

## Commit Message Guidelines

### Format

```
<type>: <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **test**: Test additions/changes
- **refactor**: Code refactoring
- **style**: Formatting changes
- **chore**: Maintenance tasks

### Examples

**Good:**
```
feat: Add /stats command to Telegram bot

Implements user statistics including:
- Active subscriptions count
- Total insights received
- Most analyzed stocks

Closes #42
```

**Bad:**
```
update stuff
```

### Rules

- Use imperative mood ("Add feature" not "Added feature")
- First line under 70 characters
- Separate subject from body with blank line
- Explain what and why, not how
- Reference issues/PRs in footer

## Common Contribution Scenarios

### Adding a New Feature

1. **Check the spec** (`specs/001-llm-stock-analyzer/`)
2. **Write contract test** (`tests/contract/`)
3. **Write unit tests** (`tests/unit/`)
4. **Verify tests FAIL**
5. **Implement feature** (`src/stock_analyzer/`)
6. **Verify tests PASS**
7. **Add CLI command** (if needed)
8. **Update documentation**
9. **Submit PR**

### Fixing a Bug

1. **Write test that reproduces bug** (should fail)
2. **Fix the bug**
3. **Verify test passes**
4. **Add regression test** (if not already covered)
5. **Submit PR**

### Improving Documentation

1. **Update relevant files** (README.md, docstrings, etc.)
2. **Verify examples work**
3. **Check links are valid**
4. **Submit PR**

## Questions?

- **General questions**: Open a [discussion](../../discussions)
- **Bug reports**: Create an [issue](../../issues/new)
- **Feature requests**: Create an [issue](../../issues/new)
- **Security issues**: See SECURITY.md (if present) or contact maintainers privately

## Additional Resources

- [Project README](README.md)
- [Constitution](.specify/memory/constitution.md)
- [Feature Specification](specs/001-llm-stock-analyzer/spec.md)
- [Implementation Plan](specs/001-llm-stock-analyzer/plan.md)
- [Task List](specs/001-llm-stock-analyzer/tasks.md)

---

**Thank you for contributing to AlphaAgent!** 🚀

Every contribution, no matter how small, helps make this project better.
