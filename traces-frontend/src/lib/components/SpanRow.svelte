<script lang="ts">
	import type { Span } from '$lib/types';
	import KindBadge from './KindBadge.svelte';
	import DurationBar from './DurationBar.svelte';

	interface Props {
		span: Span;
		maxDuration: number;
		depth?: number;
	}

	let { span, maxDuration, depth = 0 }: Props = $props();

	const isError = $derived(span.status === 'error' || span.data.is_error === true);

	function formatData(span: Span): string {
		const parts: string[] = [];

		if (span.kind === 'trace') {
			if (span.data.model) parts.push(`model: ${span.data.model}`);
			if (span.data.input_len) parts.push(`input: ${span.data.input_len} chars`);
		} else if (span.kind === 'api') {
			if (span.data.model) parts.push(`model: ${span.data.model}`);
			if (span.data.message_count) parts.push(`msgs: ${span.data.message_count}`);
			if (span.data.tool_count) parts.push(`tools: ${span.data.tool_count}`);
		} else if (span.kind === 'stream') {
			if (span.data.chunk_count) parts.push(`chunks: ${span.data.chunk_count}`);
			if (span.data.first_token_ms !== undefined) parts.push(`TTFT: ${span.data.first_token_ms.toFixed(0)}ms`);
			if (span.data.tool_call_count) parts.push(`tool calls: ${span.data.tool_call_count}`);
		} else if (span.kind === 'tool') {
			if (span.data.tool_name) parts.push(span.data.tool_name);
			if (span.data.result_len) parts.push(`result: ${span.data.result_len} chars`);
			if (span.data.error_type) parts.push(`error: ${span.data.error_type}`);
		}

		return parts.join(' · ');
	}
</script>

<div
	class="flex items-center gap-3 px-3 py-2 border-b border-gray-800 hover:bg-gray-800/50 {isError
		? 'bg-red-950/30 border-l-2 border-l-red-500'
		: ''}"
	style="padding-left: {depth * 24 + 12}px"
>
	<KindBadge kind={span.kind} />

	<div class="flex-1 min-w-0">
		<div class="flex items-center gap-2">
			<span class="text-sm text-gray-200 font-medium truncate">{span.name}</span>
			{#if isError}
				<span class="text-xs text-red-400">ERROR</span>
			{/if}
		</div>
		<div class="text-xs text-gray-500 truncate">{formatData(span)}</div>
	</div>

	<DurationBar durationMs={span.duration_ms} maxMs={maxDuration} />
</div>
