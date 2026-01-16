export type SpanKind = 'conversation' | 'turn' | 'llm' | 'tool' | 'internal';
export type SpanStatus = 'ok' | 'error' | 'running';

export interface SpanData {
	model?: string;
	input_len?: number;
	message_count?: number;
	tool_count?: number;
	chunk_count?: number;
	first_token_ms?: number;
	tool_call_count?: number;
	tool_name?: string;
	tool_call_id?: string;
	is_error?: boolean;
	result_len?: number;
	error_type?: string;
	[key: string]: string | number | boolean | undefined;
}

export interface Span {
	ts: string;
	trace_id: string;
	span_id: string;
	parent_id: string | null;
	name: string;
	kind: SpanKind;
	duration_ms: number | null;
	status: SpanStatus;
	data: SpanData;
	error: string | null;
}

export interface TraceInfo {
	trace_id: string;
	root_span_id: string | null;
	span_ids: string[];
	model: string;
	duration_ms: number | null;
	error_count: number;
	start_ts: string;
}
