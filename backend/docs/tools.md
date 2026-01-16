# Tool Development Guide

## Error Handling

**Problem**: Generic errors like `"Error executing tool: [Errno 2]..."` are not actionable. Models retry with same inputs or give up.

**Solution**: Use `ToolError` with clear, directive messages including runtime context.

```python
from src.tools.errors import ToolError

# Bad
raise ValueError(f"Invalid timezone: {tz}")

# Good
raise ToolError(f"Invalid timezone '{tz}'. Use IANA format like 'UTC' or 'America/New_York'.")
```

### Error Message Pattern

```
[What failed]. [What to do]. [Context if helpful].
```

Examples:
- `File '/foo/bar.py' not found. Check the path exists.`
- `Missing required argument 'file_path'.`
- `Path must be absolute. Got 'foo.py'. Try '/Users/yabo/project/foo.py'.`

### Why This Matters

Research on open-source agents (Aider, OpenCode, SWE-agent) shows:
- Directive language ("Include more context") works better than descriptive ("requires more context")
- Models auto-retry 2-3 times for param errors—clear messages help self-correction
- Suggestions with runtime data (actual paths, valid examples) dramatically improve recovery

### Framework Errors

The `ToolExecutor` handles these automatically:
- JSON parse errors → `"Invalid JSON in arguments. {error}."`
- Pydantic validation → `"Missing required argument 'field'."` or `"Argument 'field' must be integer."`
- Unknown tool → `"Unknown tool 'name'. Available: tool1, tool2."`

Tools only need to raise `ToolError` for domain-specific failures.

## Creating a New Tool

1. Create `src/tools/your_tool.py`
2. Define Pydantic args model with `Field(description=...)` 
3. Extend `BaseTool[YourArgs]`
4. Register in `src/tools/__init__.py`

Schema auto-generates from Pydantic model—no manual JSON schema needed.
