<script lang="ts">
	interface Props {
		durationMs: number | null;
		maxMs: number;
	}

	let { durationMs, maxMs }: Props = $props();

	const widthPercent = $derived(durationMs && maxMs > 0 ? Math.min(100, (durationMs / maxMs) * 100) : 0);

	const color = $derived(
		durationMs === null
			? 'bg-gray-400'
			: durationMs < 100
				? 'bg-green-500'
				: durationMs < 500
					? 'bg-yellow-500'
					: durationMs < 2000
						? 'bg-orange-500'
						: 'bg-red-500'
	);
</script>

<div class="flex items-center gap-2 min-w-48">
	<div class="flex-1 h-2 bg-gray-700 rounded overflow-hidden">
		<div class="h-full {color} transition-all duration-200" style="width: {widthPercent}%"></div>
	</div>
	<span class="text-xs text-gray-400 font-mono w-16 text-right">
		{#if durationMs !== null}
			{durationMs.toFixed(1)}ms
		{:else}
			-
		{/if}
	</span>
</div>
