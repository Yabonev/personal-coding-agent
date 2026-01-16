<script lang="ts">
	import type { SpanKind } from '$lib/types';
	import { spanStore } from '$lib/stores/spans.svelte';
	import SpanRow from './SpanRow.svelte';

	let autoScroll = $state(true);
	let showKinds = $state<Set<SpanKind>>(new Set(['trace', 'api', 'stream', 'tool', 'internal']));
	let errorsOnly = $state(false);

	let container: HTMLDivElement;

	const filteredSpans = $derived(
		spanStore.timeline.filter((span) => {
			if (!showKinds.has(span.kind)) return false;
			if (errorsOnly && span.status !== 'error' && !span.data.is_error) return false;
			return true;
		})
	);

	const maxDuration = $derived(Math.max(...filteredSpans.map((s) => s.duration_ms ?? 0), 1));

	$effect(() => {
		if (autoScroll && container && filteredSpans.length > 0) {
			container.scrollTop = container.scrollHeight;
		}
	});

	function toggleKind(kind: SpanKind) {
		if (showKinds.has(kind)) {
			showKinds.delete(kind);
		} else {
			showKinds.add(kind);
		}
		showKinds = new Set(showKinds);
	}

	const kinds: SpanKind[] = ['trace', 'api', 'stream', 'tool', 'internal'];
</script>

<div class="flex flex-col h-full">
	<div class="flex items-center gap-4 px-4 py-2 bg-gray-800 border-b border-gray-700">
		<span class="text-sm text-gray-400">Filters:</span>
		{#each kinds as kind}
			<button
				class="px-2 py-1 text-xs rounded {showKinds.has(kind)
					? 'bg-gray-600 text-white'
					: 'bg-gray-900 text-gray-500'}"
				onclick={() => toggleKind(kind)}
			>
				{kind.toUpperCase()}
			</button>
		{/each}
		<button
			class="px-2 py-1 text-xs rounded {errorsOnly ? 'bg-red-600 text-white' : 'bg-gray-900 text-gray-500'}"
			onclick={() => (errorsOnly = !errorsOnly)}
		>
			Errors Only
		</button>

		<div class="flex-1"></div>

		<label class="flex items-center gap-2 text-sm text-gray-400">
			<input type="checkbox" bind:checked={autoScroll} class="rounded" />
			Auto-scroll
		</label>

		<span class="text-xs text-gray-500">{filteredSpans.length} spans</span>
	</div>

	<div bind:this={container} class="flex-1 overflow-y-auto">
		{#each filteredSpans as span (span.span_id)}
			<SpanRow {span} {maxDuration} />
		{/each}
		{#if filteredSpans.length === 0}
			<div class="px-4 py-16 text-center text-gray-500">Waiting for spans...</div>
		{/if}
	</div>
</div>
