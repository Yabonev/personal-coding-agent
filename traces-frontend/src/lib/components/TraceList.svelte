<script lang="ts">
	import { spanStore } from '$lib/stores/spans.svelte';

	interface Props {
		selectedTraceId: string | null;
		onSelect: (traceId: string) => void;
	}

	let { selectedTraceId, onSelect }: Props = $props();

	const traceList = $derived(
		Array.from(spanStore.traces.values()).sort(
			(a, b) => new Date(b.start_ts).getTime() - new Date(a.start_ts).getTime()
		)
	);
</script>

<div class="h-full overflow-y-auto">
	{#each traceList as trace (trace.trace_id)}
		<button
			class="w-full text-left px-3 py-2 border-b border-gray-800 hover:bg-gray-800/50 {selectedTraceId ===
			trace.trace_id
				? 'bg-gray-700'
				: ''} {trace.error_count > 0 ? 'border-l-2 border-l-red-500' : ''}"
			onclick={() => onSelect(trace.trace_id)}
		>
			<div class="flex items-center justify-between">
				<span class="text-sm text-gray-200 font-medium truncate">
					{trace.model || 'api.request'}
				</span>
				{#if trace.error_count > 0}
					<span class="text-xs text-red-400">{trace.error_count} errors</span>
				{/if}
			</div>
			<div class="flex items-center justify-between text-xs text-gray-500 mt-1">
				<span>{trace.span_ids.length} spans</span>
				<span>
					{#if trace.duration_ms !== null}
						{trace.duration_ms.toFixed(0)}ms
					{:else}
						-
					{/if}
				</span>
			</div>
		</button>
	{/each}
	{#if traceList.length === 0}
		<div class="px-4 py-8 text-center text-gray-500">No traces yet</div>
	{/if}
</div>
