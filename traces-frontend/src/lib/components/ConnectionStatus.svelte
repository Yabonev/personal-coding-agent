<script lang="ts">
	import { spanStore } from '$lib/stores/spans.svelte';
</script>

<div class="flex items-center gap-2">
	<div
		class="w-2 h-2 rounded-full {spanStore.connected ? 'bg-green-500' : 'bg-red-500'} animate-pulse"
	></div>
	<span class="text-sm text-gray-400">
		{#if spanStore.connected}
			Connected
		{:else if spanStore.error}
			{spanStore.error}
		{:else}
			Disconnected
		{/if}
	</span>
</div>
