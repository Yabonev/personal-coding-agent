<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import type { Span } from '$lib/types';

	interface Props {
		data: {
			span: Span;
			isSelected: boolean;
			onSelect: () => void;
		};
	}

	let { data }: Props = $props();

	const span = $derived(data.span);
	const isSelected = $derived(data.isSelected);
	const isRunning = $derived(span.duration_ms === null);
	const isError = $derived(span.status === 'error');

	function getColor(): string {
		if (isRunning) return '#3b82f6';
		if (isError) return '#ef4444';
		return '#6b7280';
	}

	function formatDuration(ms: number | null): string {
		if (ms === null) return 'running';
		if (ms < 1) return '<1ms';
		if (ms < 1000) return `${ms.toFixed(0)}ms`;
		return `${(ms / 1000).toFixed(2)}s`;
	}

	function getKindLabel(kind: string): string {
		const labels: Record<string, string> = {
			conversation: 'conv',
			turn: 'turn',
			llm: 'llm',
			tool: 'tool',
			internal: 'int'
		};
		return labels[kind] || kind;
	}
</script>

<div
	class="relative group cursor-pointer"
	role="button"
	tabindex="0"
	onclick={() => data.onSelect()}
	onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') data.onSelect(); }}
>
	<div
		class="w-3 h-3 rounded-full transition-all duration-150 {isRunning ? 'animate-pulse' : ''} {isSelected ? 'ring-2 ring-white/30 scale-125' : 'hover:scale-150'}"
		style="background-color: {getColor()}"
	></div>

	<Handle type="target" position={Position.Left} class="!w-0 !h-0 !bg-transparent !border-0" />
	<Handle type="source" position={Position.Right} class="!w-0 !h-0 !bg-transparent !border-0" />

	<div class="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
		<div class="bg-neutral-800 border border-neutral-700 rounded px-2 py-1.5 text-[10px] whitespace-nowrap shadow-lg">
			<div class="flex items-center gap-2 mb-1">
				<span class="px-1 py-0.5 rounded text-[9px] font-mono" style="background-color: {getColor()}20; color: {getColor()}">
					{getKindLabel(span.kind)}
				</span>
				<span class="text-neutral-300 font-medium truncate max-w-32">{span.name}</span>
			</div>
			<div class="text-neutral-500">
				{formatDuration(span.duration_ms)}
			</div>
		</div>
	</div>
</div>
