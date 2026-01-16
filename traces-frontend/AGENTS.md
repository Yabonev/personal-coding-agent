# Traces Frontend

A SvelteKit-based trace viewer for the personal coding agent.

## Project Structure

```
traces-frontend/
├── src/
│   ├── lib/
│   │   ├── components/    # Svelte components
│   │   ├── stores/        # Reactive stores (Svelte 5 runes)
│   │   └── types.ts       # TypeScript type definitions
│   ├── routes/            # SvelteKit routes
│   └── tests/             # Test files
├── static/                # Static assets
├── svelte.config.js       # SvelteKit configuration
├── vite.config.ts         # Vite configuration
└── vitest.config.ts       # Vitest test configuration
```

## Setup

```bash
npm install
```

## Development

```bash
npm run dev
```

## Code Quality Commands

### Type Checking

```bash
npm run check
```

### Build

```bash
npm run build
```

## Testing

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch
```

## Code Style

- **Framework**: SvelteKit with Svelte 5 (runes mode)
- **Styling**: Tailwind CSS v4
- **State Management**: Svelte 5 `$state` and `$derived` runes
- **Testing**: Vitest with @testing-library/svelte

## Key Components

- **SpanStore** (`src/lib/stores/spans.svelte.ts`): Reactive store managing span data, trace info, and SSE connection
- **SpanTree** (`src/lib/components/SpanTree.svelte`): Tree view component for displaying span hierarchy
- **ConnectionStatus**: Shows SSE connection state

## SSE Connection

The frontend connects to the backend SSE endpoint at `http://127.0.0.1:8765/api/spans/stream` and fetches historical spans from `/api/spans/history` on connect/reconnect.
