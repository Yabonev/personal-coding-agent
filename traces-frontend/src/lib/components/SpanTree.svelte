<script lang="ts">
	import type { Span, SpanKind } from '$lib/types';
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

	function getBadgeStyle(span: Span): string {
		const isRunning = span.duration_ms === null;
		const isError = span.status === 'error';
		
		if (isRunning) return 'border-blue-500/50 text-blue-400/70';
		if (isError) return 'border-red-500/50 text-red-400/70';
		return 'border-emerald-600/40 text-emerald-500/60';
	}

	function getSpanDescription(span: Span): string {
		switch (span.kind) {
			case 'tool': {
				const name = span.data.tool_name || span.name;
				const arg = extractToolArg(span);
				return arg ? `${name}(${arg})` : name;
			}
			case 'llm':
				return span.data.model ? String(span.data.model) : '';
			case 'turn':
				return span.data.response_preview ? String(span.data.response_preview) : '';
			case 'conversation':
				return span.data.user_message_preview ? String(span.data.user_message_preview) : '';
			default:
				return '';
		}
	}

	function extractToolArg(span: Span): string {
		if (span.data.file_path) return shortenPath(String(span.data.file_path));
		if (span.data.path) return shortenPath(String(span.data.path));
		if (span.data.pattern) return String(span.data.pattern).slice(0, 30);
		return '';
	}

	function shortenPath(path: string): string {
		const parts = path.split('/');
		if (parts.length <= 2) return path;
		return parts.slice(-2).join('/');
	}

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
	});

	$effect(() => {
		if (traceSpans.length > 0) {
			updateExpandedSpans();
		}
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
	<div class="flex items-center gap-2 px-3 py-2 border-b border-neutral-800 text-xs text-neutral-400">
		<label class="flex items-center gap-1.5 cursor-pointer hover:text-neutral-300 transition-colors">
			<input
				type="checkbox"
				checked={autoExpand}
				onchange={toggleAutoExpand}
				class="cursor-pointer accent-indigo-500"
			/>
			Expand All
		</label>
	</div>
	<div class="flex flex-1 overflow-hidden">
	<div class="flex-1 overflow-y-auto border-r border-neutral-800">
		{#each treeItems as { span, depth } (span.span_id)}
			{@const isError = span.status === 'error'}
			{@const isRunning = span.duration_ms === null}
			{@const isSelected = selectedSpan?.span_id === span.span_id}
			{@const hasKids = hasChildren(span.span_id)}
			{@const isExpanded = expandedSpans.has(span.span_id)}
			{@const description = getSpanDescription(span)}

			<div
				class="w-full text-left flex items-center gap-2 py-1.5 px-2 hover:bg-neutral-800/30 cursor-pointer relative
					{isError ? 'border-l border-red-500/50' : 'border-l border-transparent'}
					{isSelected ? 'bg-neutral-800/50' : ''}"
				style="padding-left: {depth * 20 + 8}px"
				role="button"
				tabindex="0"
				onclick={() => selectSpan(span)}
				onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') selectSpan(span); }}
			>
				{#if depth > 0}
					<div 
						class="absolute left-0 top-0 bottom-0 pointer-events-none"
						style="left: {(depth - 1) * 20 + 16}px"
					>
						<div class="w-px h-full bg-neutral-800"></div>
						<div class="absolute top-1/2 w-3 h-px bg-neutral-800" style="left: 0"></div>
					</div>
				{/if}

				{#if hasKids}
					<button
						class="w-5 h-5 flex items-center justify-center rounded hover:bg-neutral-700/50 text-neutral-500 hover:text-neutral-300"
						aria-label={isExpanded ? 'Collapse' : 'Expand'}
						onclick={(e) => { e.stopPropagation(); toggleExpand(span.span_id); }}
					>
						<svg class="w-3 h-3 transition-transform {isExpanded ? 'rotate-90' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
						</svg>
					</button>
				{:else}
					<span class="w-5"></span>
				{/if}

				<span class="inline-flex items-center gap-1.5 px-1.5 py-0.5 rounded border text-[10px] font-mono {getBadgeStyle(span)}">
					{#if isRunning}
						<span class="w-2 h-2 border border-current border-t-transparent rounded-full animate-spin"></span>
					{/if}
					{span.kind}
				</span>

				<span class="flex-1 text-sm truncate text-neutral-400 {span.kind === 'tool' ? 'underline decoration-neutral-700 underline-offset-2' : ''}">
					{description || span.name}
				</span>

				{#if !isRunning}
					<span class="text-xs text-neutral-600 font-mono tabular-nums">
						{formatDuration(span.duration_ms)}
					</span>
				{/if}

				{#if isError}
					<span class="text-[10px] text-red-400/70">err</span>
				{/if}
			</div>
		{/each}

		{#if treeItems.length === 0}
			<div class="p-4 text-neutral-500 text-sm">No spans</div>
		{/if}
	</div>

	{#if selectedSpan}
		<div class="w-[600px] min-w-[400px] overflow-y-auto p-5 bg-neutral-900">
			<div class="space-y-5">
				<div>
					<h3 class="text-xs text-neutral-400 uppercase tracking-wider font-semibold mb-2 pb-1 border-b border-neutral-700/50">Span</h3>
					<p class="text-sm text-white font-mono">{selectedSpan.name}</p>
				</div>

				<div class="grid grid-cols-2 gap-4 text-sm">
					<div>
						<span class="text-xs text-neutral-500">kind</span>
						<p class="text-neutral-300 mt-1">
							<span class="inline-flex items-center px-1.5 py-0.5 rounded border text-[10px] font-mono {getBadgeStyle(selectedSpan)}">
								{selectedSpan.kind}
							</span>
						</p>
					</div>
					<div>
						<span class="text-xs text-neutral-500">duration</span>
						<p class="text-neutral-300 mt-1 font-mono">{formatDuration(selectedSpan.duration_ms)}</p>
					</div>
					<div>
						<span class="text-xs text-neutral-500">status</span>
						<p class="mt-1 {selectedSpan.status === 'error' ? 'text-red-400/80' : 'text-neutral-300'}">
							{selectedSpan.status}
						</p>
					</div>
					<div>
						<span class="text-xs text-neutral-500">timestamp</span>
						<p class="text-neutral-400 text-xs mt-1 font-mono">{selectedSpan.ts}</p>
					</div>
				</div>

				{#if selectedSpan.error}
					<div>
						<h3 class="text-xs text-red-400 uppercase tracking-wider font-semibold mb-2 pb-1 border-b border-red-500/30">Error</h3>
						<pre class="text-sm text-red-300 whitespace-pre-wrap font-mono bg-neutral-950 p-3 rounded">{selectedSpan.error}</pre>
					</div>
				{/if}

				{#if Object.keys(selectedSpan.data).length > 0}
					<div>
						<h3 class="text-xs text-neutral-400 uppercase tracking-wider font-semibold mb-3 pb-1 border-b border-neutral-700/50">Data</h3>
						<div class="space-y-4">
							{#each Object.entries(selectedSpan.data) as [key, value]}
								{@const fixedHeight = getFieldHeight(key)}
								<div class="relative group">
									<div class="flex items-center justify-between mb-1">
										<span class="text-xs text-neutral-400 font-medium">{key}</span>
										{#if fixedHeight}
											<button
												class="text-xs text-neutral-600 hover:text-neutral-400 opacity-0 group-hover:opacity-100 transition-opacity"
												onclick={() => resetFieldHeight(key)}
											>reset</button>
										{/if}
									</div>
									<pre
										class="text-sm text-neutral-300 whitespace-pre-wrap font-mono bg-neutral-950 p-3 rounded overflow-y-auto max-h-[600px]"
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

				<div class="pt-3 border-t border-neutral-800">
					<div class="text-xs text-neutral-500 font-mono space-y-1">
						<p><span class="text-neutral-600">trace:</span> {selectedSpan.trace_id}</p>
						<p><span class="text-neutral-600">span:</span> {selectedSpan.span_id}</p>
						{#if selectedSpan.parent_id}
							<p><span class="text-neutral-600">parent:</span> {selectedSpan.parent_id}</p>
						{/if}
					</div>
				</div>
			</div>
		</div>
	{/if}
	</div>
</div>
