<script lang="ts">
	import type { Span } from '$lib/types';
	import { onMount } from 'svelte';
	import { fade, draw } from 'svelte/transition';

	interface Props {
		spans: Span[];
		selectedSpanId: string | null;
		onSelectSpan: (span: Span) => void;
	}

	let { spans, selectedSpanId, onSelectSpan }: Props = $props();

	const LANE_HEIGHT = 28;
	const HEAD_SIZE = 3;
	const PADDING_LEFT = 30;
	const PADDING_RIGHT = 80;
	const PADDING_TOP = 24;

	let now = $state(Date.now());
	let containerWidth = $state(800);
	let container: HTMLDivElement;

	onMount(() => {
		const interval = setInterval(() => {
			now = Date.now();
		}, 50);

		const resizeObserver = new ResizeObserver((entries) => {
			containerWidth = entries[0]?.contentRect.width ?? 800;
		});
		if (container) resizeObserver.observe(container);

		return () => {
			clearInterval(interval);
			resizeObserver.disconnect();
		};
	});

	interface SpanLine {
		span: Span;
		depth: number;
		startX: number;
		endX: number;
		y: number;
		parentY: number | null;
		parentEndX: number | null;
	}

	const timelineData = $derived.by(() => {
		if (spans.length === 0) return { lines: [], elapsedMs: 0, svgHeight: 100 };

		const spanIds = new Set(spans.map(s => s.span_id));
		
		let minTs = Infinity;
		let maxEnd = 0;
		
		for (const span of spans) {
			const ts = new Date(span.ts).getTime();
			if (ts < minTs) minTs = ts;
			const endMs = span.duration_ms !== null ? ts + span.duration_ms : now;
			if (endMs > maxEnd) maxEnd = endMs;
		}

		const elapsedMs = now - minTs;
		const totalMs = Math.max(maxEnd - minTs, 1);
		const availableWidth = containerWidth - PADDING_LEFT - PADDING_RIGHT;
		const scale = availableWidth / totalMs;

		// Build parent->children map
		const childrenOf = new Map<string | null, Span[]>();
		for (const span of spans) {
			const key = span.parent_id && spanIds.has(span.parent_id) ? span.parent_id : null;
			if (!childrenOf.has(key)) childrenOf.set(key, []);
			childrenOf.get(key)!.push(span);
		}

		for (const children of childrenOf.values()) {
			children.sort((a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime());
		}

		// Calculate depth for each span (siblings share same depth)
		const spanDepth = new Map<string, number>();
		
		function assignDepth(spanId: string | null, depth: number) {
			const children = childrenOf.get(spanId) || [];
			for (const child of children) {
				spanDepth.set(child.span_id, depth);
				assignDepth(child.span_id, depth + 1);
			}
		}
		
		// Roots are at depth 0
		const roots = childrenOf.get(null) || [];
		for (const root of roots) {
			spanDepth.set(root.span_id, 0);
			assignDepth(root.span_id, 1);
		}

		const lines: SpanLine[] = [];
		const spanToLine = new Map<string, SpanLine>();
		let maxDepth = 0;

		// Process all spans
		for (const span of spans) {
			const depth = spanDepth.get(span.span_id) ?? 0;
			const startMs = new Date(span.ts).getTime();
			const endMs = span.duration_ms !== null ? startMs + span.duration_ms : now;
			
			const startX = PADDING_LEFT + (startMs - minTs) * scale;
			const endX = PADDING_LEFT + (endMs - minTs) * scale;
			const y = PADDING_TOP + depth * LANE_HEIGHT;

			// Find parent line
			let parentY: number | null = null;
			let parentEndX: number | null = null;
			
			if (span.parent_id && spanIds.has(span.parent_id)) {
				const parentSpan = spans.find(s => s.span_id === span.parent_id);
				if (parentSpan) {
					const parentDepth = spanDepth.get(parentSpan.span_id) ?? 0;
					parentY = PADDING_TOP + parentDepth * LANE_HEIGHT;
					const parentEndMs = parentSpan.duration_ms !== null 
						? new Date(parentSpan.ts).getTime() + parentSpan.duration_ms 
						: now;
					parentEndX = PADDING_LEFT + (parentEndMs - minTs) * scale;
				}
			}

			const line: SpanLine = {
				span,
				depth,
				startX,
				endX,
				y,
				parentY,
				parentEndX
			};

			lines.push(line);
			spanToLine.set(span.span_id, line);

			if (depth > maxDepth) maxDepth = depth;
		}

		const svgHeight = PADDING_TOP + (maxDepth + 1) * LANE_HEIGHT + PADDING_TOP;

		return { lines, elapsedMs, svgHeight, spanToLine };
	});

	function getColor(span: Span): string {
		if (span.duration_ms === null) return '#3b82f6';
		if (span.status === 'error') return '#ef4444';
		return '#4b5563';
	}

	// Curve down from parent to child start
	function getForkPath(parentY: number, childStartX: number, childY: number): string {
		const ctrlOffset = (childY - parentY) * 0.4;
		return `M ${childStartX} ${parentY} C ${childStartX} ${parentY + ctrlOffset}, ${childStartX} ${childY - ctrlOffset}, ${childStartX} ${childY}`;
	}

	// Curve back up from child end to parent
	function getMergePath(childEndX: number, childY: number, parentY: number, parentEndX: number): string {
		const targetX = Math.min(childEndX + 10, parentEndX);
		const ctrlOffset = (childY - parentY) * 0.4;
		return `M ${childEndX} ${childY} C ${childEndX} ${childY - ctrlOffset}, ${targetX} ${parentY + ctrlOffset}, ${targetX} ${parentY}`;
	}

	function formatTime(ms: number): string {
		const s = Math.floor(ms / 1000);
		const m = Math.floor(s / 60);
		const sec = s % 60;
		const millis = Math.floor((ms % 1000) / 100);
		if (m > 0) return `${m}:${sec.toString().padStart(2, '0')}.${millis}`;
		return `${sec}.${millis}s`;
	}

	const runningHead = $derived.by(() => {
		const running = timelineData.lines.filter(l => l.span.duration_ms === null);
		if (running.length === 0) return null;
		return running.reduce((max, l) => l.endX > max.endX ? l : max, running[0]);
	});
</script>

<div class="w-full h-full bg-neutral-950 overflow-hidden" bind:this={container}>
	{#if spans.length > 0}
		<svg 
			width={containerWidth} 
			height={timelineData.svgHeight}
			class="block"
		>
			<!-- Fork curves from parent down to child -->
			{#each timelineData.lines as line (line.span.span_id + '-fork')}
				{#if line.parentY !== null}
					<path 
						d={getForkPath(line.parentY, line.startX, line.y)}
						fill="none"
						stroke="#333"
						stroke-width="1"
						in:draw={{ duration: 300 }}
					/>
				{/if}
			{/each}

			<!-- Merge curves from child end back up to parent -->
			{#each timelineData.lines as line (line.span.span_id + '-merge')}
				{#if line.parentY !== null && line.parentEndX !== null && line.span.duration_ms !== null}
					<path 
						d={getMergePath(line.endX, line.y, line.parentY, line.parentEndX)}
						fill="none"
						stroke="#333"
						stroke-width="1"
						opacity="0.5"
						in:draw={{ duration: 300, delay: 100 }}
					/>
				{/if}
			{/each}

			<!-- Span lines -->
			{#each timelineData.lines as line (line.span.span_id)}
				{@const isSelected = selectedSpanId === line.span.span_id}
				{@const isRunning = line.span.duration_ms === null}
				{@const color = getColor(line.span)}

				<!-- Horizontal span line -->
				<line 
					x1={line.startX} 
					y1={line.y} 
					x2={line.endX} 
					y2={line.y}
					stroke={color}
					stroke-width={isSelected ? 2 : 1}
					stroke-linecap="round"
					class="cursor-pointer"
					opacity={isRunning ? 0.8 : 1}
					role="button"
					tabindex="0"
					onclick={() => onSelectSpan(line.span)}
					onkeydown={(e) => { if (e.key === 'Enter') onSelectSpan(line.span); }}
					in:draw={{ duration: 200 }}
				/>

				<!-- Start node -->
				<circle 
					cx={line.startX} 
					cy={line.y} 
					r={isSelected ? HEAD_SIZE + 1 : HEAD_SIZE}
					fill={color}
					class="cursor-pointer"
					role="button"
					tabindex="0"
					onclick={() => onSelectSpan(line.span)}
					onkeydown={(e) => { if (e.key === 'Enter') onSelectSpan(line.span); }}
					in:fade={{ duration: 150 }}
				/>

				<!-- End node (if completed) -->
				{#if !isRunning}
					<circle 
						cx={line.endX} 
						cy={line.y} 
						r={HEAD_SIZE - 1}
						fill={color}
						class="cursor-pointer"
						role="button"
						tabindex="0"
						onclick={() => onSelectSpan(line.span)}
						onkeydown={(e) => { if (e.key === 'Enter') onSelectSpan(line.span); }}
						in:fade={{ duration: 150, delay: 200 }}
					/>
				{/if}

				<!-- Running head with glow -->
				{#if isRunning}
					<circle 
						cx={line.endX} 
						cy={line.y} 
						r={HEAD_SIZE + 2}
						fill={color}
						opacity="0.3"
						class="animate-pulse"
					/>
					<circle 
						cx={line.endX} 
						cy={line.y} 
						r={HEAD_SIZE}
						fill={color}
					/>
				{/if}
			{/each}

			<!-- Time label following the rightmost running head -->
			{#if runningHead}
				<text 
					x={runningHead.endX + 10} 
					y={runningHead.y + 4} 
					fill="#3b82f6" 
					font-size="11" 
					font-family="monospace"
					in:fade={{ duration: 100 }}
				>
					{formatTime(timelineData.elapsedMs)}
				</text>
			{/if}
		</svg>
	{:else}
		<div class="h-full flex items-center justify-center text-neutral-600 text-xs">
			No spans
		</div>
	{/if}
</div>
