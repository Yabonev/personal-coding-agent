import type { Span, TraceInfo } from '$lib/types';

export class SpanStore {
	spansById = $state<Map<string, Span>>(new Map());
	childrenByParent = $state<Map<string | null, string[]>>(new Map());
	traces = $state<Map<string, TraceInfo>>(new Map());
	timeline = $state<Span[]>([]);

	connected = $state(false);
	error = $state<string | null>(null);

	private eventSource: EventSource | null = null;

	addSpan(span: Span) {
		const existing = this.spansById.get(span.span_id);
		const isUpdate = existing !== undefined;

		const newSpansById = new Map(this.spansById);
		newSpansById.set(span.span_id, span);
		this.spansById = newSpansById;

		if (!isUpdate) {
			this.timeline = [...this.timeline, span];

			const parentKey = span.parent_id ?? null;
			const newChildrenByParent = new Map(this.childrenByParent);
			const existingChildren = newChildrenByParent.get(parentKey) ?? [];
			newChildrenByParent.set(parentKey, [...existingChildren, span.span_id]);
			this.childrenByParent = newChildrenByParent;
		}

		const newTraces = new Map(this.traces);
		let traceInfo = newTraces.get(span.trace_id);
		if (!traceInfo) {
			traceInfo = {
				trace_id: span.trace_id,
				root_span_id: null,
				span_ids: [],
				model: '',
				duration_ms: null,
				error_count: 0,
				start_ts: span.ts
			};
		}

		if (!isUpdate) {
			traceInfo = { ...traceInfo, span_ids: [...traceInfo.span_ids, span.span_id] };
		}

		if (span.parent_id === null) {
			traceInfo.root_span_id = span.span_id;
			traceInfo.duration_ms = span.duration_ms;
		}

		if (span.kind === 'turn' && span.data.model && !traceInfo.model) {
			traceInfo.model = String(span.data.model);
		}

		if (span.status === 'error' && (!existing || existing.status !== 'error')) {
			traceInfo = { ...traceInfo, error_count: traceInfo.error_count + 1 };
		}

		newTraces.set(span.trace_id, traceInfo);
		this.traces = newTraces;
	}

	getChildren(parentId: string | null): Span[] {
		const childIds = this.childrenByParent.get(parentId) ?? [];
		return childIds.map((id) => this.spansById.get(id)).filter((s): s is Span => s !== undefined);
	}

	getTraceSpans(traceId: string): Span[] {
		const info = this.traces.get(traceId);
		if (!info) return [];
		return info.span_ids.map((id) => this.spansById.get(id)).filter((s): s is Span => s !== undefined);
	}

	async loadHistory(baseUrl: string) {
		try {
			const response = await fetch(`${baseUrl}/api/spans/history`);
			const data = await response.json();
			for (const span of data.spans) {
				this.addSpan(span);
			}
		} catch (e) {
			console.error('Failed to load history:', e);
		}
	}

	private async fetchHistory(streamUrl: string) {
		const historyUrl = streamUrl.replace('/api/spans/stream', '/api/spans/history');
		this.clear();
		await this.loadHistory(historyUrl.replace('/api/spans/history', ''));
	}

	connect(url: string) {
		if (this.eventSource) {
			this.eventSource.close();
		}

		this.error = null;
		this.eventSource = new EventSource(url);

		this.eventSource.onopen = async () => {
			this.connected = true;
			this.error = null;
			await this.fetchHistory(url);
		};

		this.eventSource.addEventListener('span', (event) => {
			try {
				const span: Span = JSON.parse(event.data);
				this.addSpan(span);
			} catch (e) {
				console.error('Failed to parse span event:', e);
			}
		});

		this.eventSource.onerror = () => {
			this.connected = false;
			this.error = 'Connection lost. Retrying...';
		};
	}

	disconnect() {
		if (this.eventSource) {
			this.eventSource.close();
			this.eventSource = null;
		}
		this.connected = false;
	}

	clear() {
		this.spansById = new Map();
		this.childrenByParent = new Map();
		this.traces = new Map();
		this.timeline = [];
	}
}

export const spanStore = new SpanStore();
