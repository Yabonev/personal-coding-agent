# Personal Coding Agent - Backend

A Python-based personal coding agent that provides an interactive chat interface powered by AI.

## Project Structure

```
backend/
├── src/
│   ├── config/          # Configuration services
│   ├── models/          # Data models
│   ├── orchestrators/   # Chat orchestration logic
│   ├── processors/      # Stream response processing
│   ├── services/        # API and repository services
│   └── ui/              # Console output and UI components
├── tests/               # Test suite
├── main.py              # Application entry point
└── pyproject.toml       # Project configuration
```

## Setup

```bash
# Install dependencies (including dev tools)
uv sync --extra dev
```

## Running the Application

```bash
uv run python main.py
```

## Code Quality Commands

### Formatting (Black)

```bash
# Check formatting
uv run black --check .

# Auto-format code
uv run black .
```

### Linting (Ruff)

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format imports only
uv run ruff check --select I --fix .
```

### Type Checking (Mypy)

```bash
# Check types
uv run mypy src/
```

### Run All Checks

```bash
uv run black --check . && uv run ruff check . && uv run mypy src/
```

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/test_chat_api_service.py

# Run tests matching pattern
uv run pytest -k "test_initialization"

# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration
```

## Code Style

- **Formatter**: Black (line-length: 88)
- **Linter**: Ruff with ALL rules enabled (strictest settings)
- **Type Checker**: Mypy in strict mode
- All functions must have type annotations
- Imports must include `from __future__ import annotations`
- No explicit `Any` types allowed
- Generic types must have type parameters

## Code Analysis (llm-tldr)

Token-efficient code analysis tool. Use these commands to understand the codebase without reading full files.

### Understanding Structure

```bash
# Get all classes, functions, imports (without file contents)
tldr structure . --lang python

# Show file tree
tldr tree src/

# Detect architectural layers
tldr arch .
```

### Before Making Changes

```bash
# Find all callers of a function (impact analysis)
tldr impact . function_name

# Build cross-file call graph
tldr calls .

# Get relevant context for a specific entrypoint
tldr context ChatOrchestrator --project .
```

### After Making Changes

```bash
# Find tests affected by changes
tldr change-impact .

# Search for patterns
tldr search "def process" .
```

### When to Use

- **Before editing**: `tldr structure src/` to understand what exists
- **Before refactoring**: `tldr impact . func_name` to see what might break
- **For focused context**: `tldr context ClassName` instead of reading many files
- **After changes**: `tldr change-impact .` to know which tests to run
