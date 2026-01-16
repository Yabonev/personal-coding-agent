# Improvements

## Use llm-tldr Python API instead of subprocess

**Context**: The `read_file` tool adds `[used_by: ...]` frontmatter showing which files import the file being read. This helps the LLM understand the file's place in the codebase without searching.

**Problem**: Currently uses `subprocess.run(["tldr", "importers", ...])` which:
- Spawns a new process per read
- Requires `tldr` CLI to be in PATH
- Has overhead from JSON serialization/parsing
- Needs noqa comments for security linters (S603, S607)

**Solutions**:

1. **Direct API** (recommended):
   ```python
   from tldr.api import get_imports, scan_project_files
   
   files = scan_project_files(project_root, language="python")
   for f in files:
       imports = get_imports(f, language="python")
       # check if target module is in imports
   ```

2. **MCP server function**:
   ```python
   from tldr.mcp_server import importers
   result = importers(project=".", module="message_repository", language="python")
   # result["importers"] contains the list
   ```

3. **Cached queries** (best for repeated calls):
   ```python
   from tldr.daemon.cached_queries import cached_importers
   from tldr.salsa import SalsaDB
   
   db = SalsaDB()
   result = db.query(cached_importers, db, project=".", module="...", language="python")
   ```

**Status**: Investigated - `llm-tldr` base package brings 87 dependencies including torch (71MB), transformers, scipy, etc. No minimal install option exists.

**Decision**: Keep subprocess approach. The CLI is already installed separately and avoids bloating the project with ~16GB of AI dependencies.
