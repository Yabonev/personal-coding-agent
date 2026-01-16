<script lang="ts">
	import type { Span } from '$lib/types';
	import { spanStore } from '$lib/stores/spans.svelte';
	import SpanRow from './SpanRow.svelte';

	interface Props {
		traceId: string;
	}

	let { traceId }: Props = $props();

	const traceSpans = $derived(spanStore.getTraceSpans(traceId));
	const maxDuration = $derived(Math.max(...traceSpans.map((s) => s.duration_ms ?? 0), 1));

	function buildTree(parentId: string | null, depth: number): Array<{ span: Span; depth: number }> {
		const children = spanStore.getChildren(parentId).filter((s) => s.trace_id === traceId);
		const result: Array<{ span: Span; depth: number }> = [];

		for (const span of children) {
			result.push({ span, depth });
			result.push(...buildTree(span.span_id, depth + 1));
		}

		return result;
	}

	const treeItems = $derived(buildTree(null, 0));
</script>

<div class="border border-gray-800 rounded-lg overflow-hidden">
	{#each treeItems as item (item.span.span_id)}
		<SpanRow span={item.span} {maxDuration} depth={item.depth} />
	{/each}
	{#if treeItems.length === 0}
		<div class="px-4 py-8 text-center text-gray-500">No spans in this trace</div>
	{/if}
</div>
