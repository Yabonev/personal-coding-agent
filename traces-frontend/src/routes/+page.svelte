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
	<header class="flex items-center justify-between px-4 py-2 border-b border-neutral-800">
		<h1 class="text-sm font-medium text-neutral-300">Traces</h1>

		<div class="flex items-center gap-3">
			<div class="flex items-center gap-2">
				<div
					class="w-1.5 h-1.5 rounded-full {spanStore.connected ? 'bg-emerald-500' : 'bg-red-500'}"
				></div>
				<span class="text-xs text-neutral-500">
					{spanStore.connected ? 'Connected' : 'Disconnected'}
				</span>
			</div>

			<button
				class="px-2 py-1 text-xs text-neutral-400 hover:text-white border border-neutral-700 rounded"
				onclick={() => spanStore.clear()}
			>
				Clear
			</button>
		</div>
	</header>

	<main class="flex-1 flex overflow-hidden">
		<aside class="w-48 border-r border-neutral-800 overflow-y-auto">
			{#each traceList as trace (trace.trace_id)}
				{@const isSelected = selectedTraceId === trace.trace_id}
				<button
					class="w-full text-left px-3 py-2 border-b border-neutral-800/50 hover:bg-neutral-800/50
						{isSelected ? 'bg-neutral-800' : ''}
						{trace.error_count > 0 ? 'border-l-2 border-l-red-500' : ''}"
					onclick={() => (selectedTraceId = trace.trace_id)}
				>
					<div class="text-xs text-neutral-400 font-mono truncate">{trace.trace_id}</div>
					<div class="text-xs text-neutral-600 mt-0.5">{trace.span_ids.length} spans</div>
				</button>
			{/each}

			{#if traceList.length === 0}
				<div class="p-3 text-xs text-neutral-600">Waiting for traces...</div>
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
