# Trace Viewer

Real-time trace visualization UI for the personal coding agent.

## Setup

```bash
npm install
npm run dev
```

The UI will be available at http://localhost:5173

## Features

- **Timeline View**: Real-time append-only list of spans as they complete
  - Filter by span kind (TRACE, API, STREAM, TOOL, INTERNAL)
  - Filter to errors only
  - Auto-scroll toggle
  - Duration bars with color coding

- **Traces View**: Hierarchical tree view
  - List of traces sorted by recency
  - Expandable tree showing parent-child relationships
  - Error highlighting

## Connecting to Backend

The UI connects via SSE to `http://127.0.0.1:8765/api/spans/stream` by default.

To enable SSE in the backend:

```python
from src.tracing import TracingConfig, SSEServer

# Use SQLite sink with SSE enabled
config = TracingConfig.sqlite(sse_enabled=True)

# Start the SSE server
sse_server = SSEServer(port=8765)
sse_server.start()
```

## Span Data Visualization

Each span type shows relevant fields:

| Kind | Fields |
|------|--------|
| TRACE | model, input_len, duration |
| API | model, message_count, tool_count, duration |
| STREAM | chunk_count, first_token_ms (TTFT), tool_call_count, duration |
| TOOL | tool_name, result_len, error_type, duration |

## Development

```bash
npm run dev      # Start dev server
npm run build    # Production build
npm run preview  # Preview production build
```
