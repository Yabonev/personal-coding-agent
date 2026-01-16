import { describe, it, expect, beforeEach } from 'vitest';
import type { Span } from '$lib/types';

function createSpan(overrides: Partial<Span> = {}): Span {
	return {
		ts: new Date().toISOString(),
		trace_id: 'tr_test',
		span_id: `sp_${Math.random().toString(36).slice(2, 14)}`,
		parent_id: null,
		name: 'test-span',
		kind: 'internal',
		duration_ms: null,
		status: 'ok',
		data: {},
		error: null,
		...overrides
	};
}

describe('SpanStore', () => {
	let SpanStore: typeof import('$lib/stores/spans.svelte').SpanStore;

	beforeEach(async () => {
		const module = await import('$lib/stores/spans.svelte');
		SpanStore = module.SpanStore;
	});

	describe('addSpan', () => {
		it('adds a new span to spansById', () => {
			const store = new SpanStore();
			const span = createSpan({ span_id: 'sp_001' });

			store.addSpan(span);

			expect(store.spansById.get('sp_001')).toEqual(span);
		});

		it('updates existing span without duplicating in timeline', () => {
			const store = new SpanStore();
			const span1 = createSpan({ span_id: 'sp_001', status: 'running' });
			const span2 = createSpan({ span_id: 'sp_001', status: 'ok', duration_ms: 100 });

			store.addSpan(span1);
			store.addSpan(span2);

			expect(store.timeline.length).toBe(1);
			expect(store.spansById.get('sp_001')?.status).toBe('ok');
			expect(store.spansById.get('sp_001')?.duration_ms).toBe(100);
		});

		it('creates trace info for new trace', () => {
			const store = new SpanStore();
			const span = createSpan({ trace_id: 'tr_001', span_id: 'sp_001' });

			store.addSpan(span);

			const traceInfo = store.traces.get('tr_001');
			expect(traceInfo).toBeDefined();
			expect(traceInfo?.span_ids).toContain('sp_001');
		});

		it('tracks root span (parent_id null)', () => {
			const store = new SpanStore();
			const rootSpan = createSpan({
				trace_id: 'tr_001',
				span_id: 'sp_root',
				parent_id: null,
				duration_ms: 500
			});

			store.addSpan(rootSpan);

			const traceInfo = store.traces.get('tr_001');
			expect(traceInfo?.root_span_id).toBe('sp_root');
			expect(traceInfo?.duration_ms).toBe(500);
		});

		it('tracks children by parent', () => {
			const store = new SpanStore();
			const parent = createSpan({ span_id: 'sp_parent', parent_id: null });
			const child1 = createSpan({ span_id: 'sp_child1', parent_id: 'sp_parent' });
			const child2 = createSpan({ span_id: 'sp_child2', parent_id: 'sp_parent' });

			store.addSpan(parent);
			store.addSpan(child1);
			store.addSpan(child2);

			const children = store.childrenByParent.get('sp_parent');
			expect(children).toContain('sp_child1');
			expect(children).toContain('sp_child2');
		});

		it('increments error count on error status', () => {
			const store = new SpanStore();
			const span = createSpan({
				trace_id: 'tr_001',
				span_id: 'sp_001',
				status: 'error'
			});

			store.addSpan(span);

			const traceInfo = store.traces.get('tr_001');
			expect(traceInfo?.error_count).toBe(1);
		});

		it('captures model from turn span', () => {
			const store = new SpanStore();
			const span = createSpan({
				trace_id: 'tr_001',
				kind: 'turn',
				data: { model: 'gpt-4' }
			});

			store.addSpan(span);

			const traceInfo = store.traces.get('tr_001');
			expect(traceInfo?.model).toBe('gpt-4');
		});
	});

	describe('getTraceSpans', () => {
		it('returns empty array for unknown trace', () => {
			const store = new SpanStore();
			expect(store.getTraceSpans('unknown')).toEqual([]);
		});

		it('returns all spans for a trace', () => {
			const store = new SpanStore();
			const span1 = createSpan({ trace_id: 'tr_001', span_id: 'sp_001' });
			const span2 = createSpan({ trace_id: 'tr_001', span_id: 'sp_002' });
			const span3 = createSpan({ trace_id: 'tr_002', span_id: 'sp_003' });

			store.addSpan(span1);
			store.addSpan(span2);
			store.addSpan(span3);

			const spans = store.getTraceSpans('tr_001');
			expect(spans.length).toBe(2);
			expect(spans.map(s => s.span_id)).toContain('sp_001');
			expect(spans.map(s => s.span_id)).toContain('sp_002');
		});
	});

	describe('getChildren', () => {
		it('returns children of a parent span', () => {
			const store = new SpanStore();
			const parent = createSpan({ span_id: 'sp_parent' });
			const child = createSpan({ span_id: 'sp_child', parent_id: 'sp_parent' });

			store.addSpan(parent);
			store.addSpan(child);

			const children = store.getChildren('sp_parent');
			expect(children.length).toBe(1);
			expect(children[0].span_id).toBe('sp_child');
		});

		it('returns root spans for null parent', () => {
			const store = new SpanStore();
			const root = createSpan({ span_id: 'sp_root', parent_id: null });

			store.addSpan(root);

			const roots = store.getChildren(null);
			expect(roots.length).toBe(1);
			expect(roots[0].span_id).toBe('sp_root');
		});
	});

	describe('clear', () => {
		it('clears all data', () => {
			const store = new SpanStore();
			store.addSpan(createSpan({ trace_id: 'tr_001' }));

			store.clear();

			expect(store.spansById.size).toBe(0);
			expect(store.traces.size).toBe(0);
			expect(store.timeline.length).toBe(0);
			expect(store.childrenByParent.size).toBe(0);
		});
	});
});
