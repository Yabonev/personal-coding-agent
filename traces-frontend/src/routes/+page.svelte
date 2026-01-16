<script lang="ts">
	import { onMount } from 'svelte';
	import { spanStore } from '$lib/stores/spans.svelte';
	import SpanTree from '$lib/components/SpanTree.svelte';

	const baseUrl = 'http://127.0.0.1:8765';
	let sseUrl = $state(`${baseUrl}/api/spans/stream`);

	const traceList = $derived(
		Array.from(spanStore.traces.values()).sort(
			(a, b) => new Date(b.start_ts).getTime() - new Date(a.start_ts).getTime()
		)
	);

	let selectedTraceId = $state<string | null>(null);

	$effect(() => {
		if (traceList.length > 0 && !selectedTraceId) {
			selectedTraceId = traceList[0].trace_id;
		}
	});

	onMount(() => {
		spanStore.loadHistory(baseUrl).then(() => {
			spanStore.connect(sseUrl);
		});
		return () => spanStore.disconnect();
	});

</script>

<div class="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col">
	<header class="flex items-center justify-between px-5 py-3 border-b border-neutral-800 bg-gradient-to-r from-neutral-900 to-neutral-950">
		<h1 class="text-base font-semibold text-white tracking-tight">Traces</h1>

		<div class="flex items-center gap-4">
			<div class="flex items-center gap-2">
				<div
					class="w-2 h-2 rounded-full {spanStore.connected ? 'bg-emerald-500 shadow-sm shadow-emerald-500/50' : 'bg-red-500 shadow-sm shadow-red-500/50'}"
				></div>
				<span class="text-xs text-neutral-400">
					{spanStore.connected ? 'Connected' : 'Disconnected'}
				</span>
			</div>

			<button
				class="px-3 py-1.5 text-xs text-neutral-300 hover:text-white border border-neutral-700 hover:border-neutral-600 rounded transition-colors"
				onclick={() => spanStore.clear()}
			>
				Clear
			</button>
		</div>
	</header>

	<main class="flex-1 flex overflow-hidden">
		<aside class="w-52 border-r border-neutral-800 overflow-y-auto bg-neutral-900/30">
			{#each traceList as trace, index (trace.trace_id)}
				{@const isSelected = selectedTraceId === trace.trace_id}
				{@const traceNumber = traceList.length - index}
				{@const timestamp = new Date(trace.start_ts)}
				<button
					class="w-full text-left px-3 py-2.5 border-b border-neutral-800/50 hover:bg-neutral-800/50 transition-colors
						{isSelected ? 'bg-neutral-800' : ''}
						{trace.error_count > 0 ? 'border-l-2 border-l-red-500' : 'border-l-2 border-l-transparent'}"
					onclick={() => (selectedTraceId = trace.trace_id)}
				>
					<div class="text-sm text-neutral-200 font-medium">Conversation {traceNumber}</div>
					<div class="flex items-center gap-2 mt-1">
						<span class="text-xs text-neutral-500">{trace.span_ids.length} spans</span>
						<span class="text-neutral-700">·</span>
						<span class="text-xs text-neutral-500">{timestamp.toLocaleTimeString()}</span>
					</div>
				</button>
			{/each}

			{#if traceList.length === 0}
				<div class="p-4 text-sm text-neutral-500">No traces yet</div>
			{/if}
		</aside>

		<div class="flex-1 overflow-hidden">
			{#if selectedTraceId}
				<SpanTree traceId={selectedTraceId} />
			{:else}
				<div class="h-full flex items-center justify-center text-neutral-600 text-sm">
					Select a trace
				</div>
			{/if}
		</div>
	</main>
</div>
