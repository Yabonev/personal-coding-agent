<script lang="ts">
	import type { Span } from '$lib/types';
	import { spanStore } from '$lib/stores/spans.svelte';
	import { onMount } from 'svelte';

	interface Props {
		traceId: string;
	}

	let { traceId }: Props = $props();
	let expandedSpans = $state<Set<string>>(new Set());
	let selectedSpan = $state<Span | null>(null);
	let autoExpand = $state<boolean>(true);

	const STORAGE_KEY = 'trace-viewer-field-heights';
	const AUTO_EXPAND_KEY = 'trace-viewer-auto-expand';

	let fieldHeights = $state<Record<string, number>>({});

	onMount(() => {
		const stored = localStorage.getItem(STORAGE_KEY);
		if (stored) {
			try {
				fieldHeights = JSON.parse(stored);
			} catch {
				fieldHeights = {};
			}
		}

		const storedAutoExpand = localStorage.getItem(AUTO_EXPAND_KEY);
		if (storedAutoExpand !== null) {
			autoExpand = storedAutoExpand === 'true';
		}
		updateExpandedSpans();
	});

	function updateExpandedSpans() {
		if (autoExpand) {
			const allParentIds = new Set(
				traceSpans.filter((s) => traceSpans.some((child) => child.parent_id === s.span_id)).map((s) => s.span_id)
			);
			expandedSpans = allParentIds;
		} else {
			expandedSpans = new Set();
		}
	}

	function toggleAutoExpand() {
		autoExpand = !autoExpand;
		localStorage.setItem(AUTO_EXPAND_KEY, String(autoExpand));
		updateExpandedSpans();
	}

	function getFieldHeight(key: string): number | null {
		return fieldHeights[key] ?? null;
	}

	function saveHeights() {
		localStorage.setItem(STORAGE_KEY, JSON.stringify(fieldHeights));
	}

	function resetFieldHeight(key: string) {
		const { [key]: _, ...rest } = fieldHeights;
		fieldHeights = rest;
		saveHeights();
	}

	let resizing = $state<{ key: string; startY: number; startHeight: number } | null>(null);

	function startResize(key: string, e: MouseEvent, currentHeight: number) {
		e.preventDefault();
		resizing = { key, startY: e.clientY, startHeight: currentHeight };
	}

	function onMouseMove(e: MouseEvent) {
		if (!resizing) return;
		const delta = e.clientY - resizing.startY;
		const newHeight = Math.max(50, resizing.startHeight + delta);
		fieldHeights = { ...fieldHeights, [resizing.key]: newHeight };
	}

	function onMouseUp() {
		if (resizing) {
			saveHeights();
			resizing = null;
		}
	}

	const traceSpans = $derived(spanStore.getTraceSpans(traceId));

	function buildTree(spans: Span[], parentId: string | null, depth: number): Array<{ span: Span; depth: number }> {
		const children = spans.filter((s) => s.parent_id === parentId);
		const result: Array<{ span: Span; depth: number }> = [];

		for (const span of children) {
			result.push({ span, depth });
			if (expandedSpans.has(span.span_id)) {
				result.push(...buildTree(spans, span.span_id, depth + 1));
			}
		}
		return result;
	}

	const treeItems = $derived.by(() => {
		const spanIds = new Set(traceSpans.map(s => s.span_id));
		const localRoots = traceSpans.filter(s => s.parent_id === null || !spanIds.has(s.parent_id));
		
		const result: Array<{ span: Span; depth: number }> = [];
		for (const root of localRoots) {
			result.push({ span: root, depth: 0 });
			if (expandedSpans.has(root.span_id)) {
				result.push(...buildTree(traceSpans, root.span_id, 1));
			}
		}
		return result;
	});

	function hasChildren(spanId: string): boolean {
		return traceSpans.filter((s) => s.parent_id === spanId).length > 0;
	}

	function toggleExpand(spanId: string) {
		if (expandedSpans.has(spanId)) {
			expandedSpans.delete(spanId);
		} else {
			expandedSpans.add(spanId);
		}
		expandedSpans = new Set(expandedSpans);
	}

	function selectSpan(span: Span) {
		selectedSpan = selectedSpan?.span_id === span.span_id ? null : span;
	}

	function formatDuration(ms: number | null): string {
		if (ms === null) return '-';
		if (ms < 1) return '<1ms';
		if (ms < 1000) return `${ms.toFixed(0)}ms`;
		return `${(ms / 1000).toFixed(2)}s`;
	}

	function formatDataValue(value: unknown): string {
		if (typeof value === 'string') {
			try {
				const parsed = JSON.parse(value);
				return JSON.stringify(parsed, null, 2);
			} catch {
				return value;
			}
		}
		if (typeof value === 'object' && value !== null) {
			return JSON.stringify(value, null, 2);
		}
		return String(value);
	}
</script>

<svelte:window onmousemove={onMouseMove} onmouseup={onMouseUp} />

<div class="flex h-full flex-col">
	<div class="flex items-center gap-2 px-2 py-1.5 border-b border-neutral-800 text-xs text-neutral-400">
		<label class="flex items-center gap-1.5 cursor-pointer">
			<input
				type="checkbox"
				checked={autoExpand}
				onchange={toggleAutoExpand}
				class="cursor-pointer"
			/>
			Auto-expand
		</label>
	</div>
	<div class="flex flex-1 overflow-hidden">
	<div class="flex-1 overflow-y-auto border-r border-neutral-800">
		{#each treeItems as { span, depth } (span.span_id)}
			{@const isError = span.status === 'error'}
			{@const isSelected = selectedSpan?.span_id === span.span_id}
			{@const hasKids = hasChildren(span.span_id)}
			{@const isExpanded = expandedSpans.has(span.span_id)}

			<div
				class="w-full text-left flex items-center gap-2 py-1.5 px-2 hover:bg-neutral-800/50 border-l-2 cursor-pointer
					{isError ? 'border-red-500' : 'border-transparent'}
					{isSelected ? 'bg-neutral-800' : ''}"
				style="padding-left: {depth * 16 + 8}px"
				role="button"
				tabindex="0"
				onclick={() => selectSpan(span)}
				onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') selectSpan(span); }}
			>
				{#if hasKids}
					<span
						class="w-4 h-4 flex items-center justify-center text-neutral-500 hover:text-white cursor-pointer"
						role="button"
						tabindex="0"
						onclick={(e) => { e.stopPropagation(); toggleExpand(span.span_id); }}
						onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.stopPropagation(); toggleExpand(span.span_id); } }}
					>
						{isExpanded ? '▼' : '▶'}
					</span>
				{:else}
					<span class="w-4"></span>
				{/if}

				<span class="text-neutral-500 text-xs font-mono w-12">{span.kind}</span>

				<span class="flex-1 text-sm text-neutral-200 truncate">
					{span.name}
					{#if span.data.tool_name}
						<span class="text-neutral-400">({span.data.tool_name})</span>
					{/if}
				</span>

				<span class="text-xs text-neutral-500 font-mono">
					{formatDuration(span.duration_ms)}
				</span>

				{#if isError}
					<span class="text-xs text-red-400">ERR</span>
				{/if}
			</div>
		{/each}

		{#if treeItems.length === 0}
			<div class="p-4 text-neutral-500 text-sm">No spans</div>
		{/if}
	</div>

	{#if selectedSpan}
		<div class="w-[600px] min-w-[400px] overflow-y-auto p-4 bg-neutral-900">
			<div class="space-y-4">
				<div>
					<h3 class="text-xs text-neutral-500 uppercase tracking-wide mb-1">Span</h3>
					<p class="text-sm text-white font-mono">{selectedSpan.name}</p>
				</div>

				<div class="grid grid-cols-2 gap-3 text-sm">
					<div>
						<span class="text-neutral-500">Kind</span>
						<p class="text-neutral-200">{selectedSpan.kind}</p>
					</div>
					<div>
						<span class="text-neutral-500">Duration</span>
						<p class="text-neutral-200">{formatDuration(selectedSpan.duration_ms)}</p>
					</div>
					<div>
						<span class="text-neutral-500">Status</span>
						<p class="{selectedSpan.status === 'error' ? 'text-red-400' : 'text-neutral-200'}">
							{selectedSpan.status}
						</p>
					</div>
					<div>
						<span class="text-neutral-500">Timestamp</span>
						<p class="text-neutral-200 text-xs">{selectedSpan.ts}</p>
					</div>
				</div>

				{#if selectedSpan.error}
					<div>
						<h3 class="text-xs text-red-400 uppercase tracking-wide mb-1">Error</h3>
						<pre class="text-sm text-red-300 whitespace-pre-wrap font-mono bg-neutral-950 p-2 rounded">{selectedSpan.error}</pre>
					</div>
				{/if}

				{#if Object.keys(selectedSpan.data).length > 0}
					<div>
						<h3 class="text-xs text-neutral-500 uppercase tracking-wide mb-2">Data</h3>
						<div class="space-y-3">
							{#each Object.entries(selectedSpan.data) as [key, value]}
								{@const fixedHeight = getFieldHeight(key)}
								<div class="relative group">
									<div class="flex items-center justify-between">
										<span class="text-xs text-neutral-500">{key}</span>
										{#if fixedHeight}
											<button
												class="text-xs text-neutral-600 hover:text-neutral-400 opacity-0 group-hover:opacity-100"
												onclick={() => resetFieldHeight(key)}
											>reset</button>
										{/if}
									</div>
									<pre
										class="text-sm text-neutral-300 whitespace-pre-wrap font-mono bg-neutral-950 p-2 rounded mt-0.5 overflow-y-auto max-h-[600px]"
										style={fixedHeight ? `height: ${fixedHeight}px` : ''}
									>{formatDataValue(value)}</pre>
									<!-- svelte-ignore a11y_no_static_element_interactions -->
									<div
										class="absolute bottom-0 left-0 right-0 h-2 cursor-ns-resize hover:bg-neutral-700/50 flex items-center justify-center"
										onmousedown={(e) => {
											const pre = e.currentTarget.previousElementSibling as HTMLElement;
											startResize(key, e, pre?.offsetHeight ?? 100);
										}}
									>
										<div class="w-8 h-0.5 bg-neutral-600 rounded"></div>
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<div class="text-xs text-neutral-600 font-mono space-y-1">
					<p>trace: {selectedSpan.trace_id}</p>
					<p>span: {selectedSpan.span_id}</p>
					{#if selectedSpan.parent_id}
						<p>parent: {selectedSpan.parent_id}</p>
					{/if}
				</div>
			</div>
		</div>
	{/if}
	</div>
</div>
