<script lang="ts">
	import '../app.css';

	let { children } = $props();
</script>

<svelte:head>
	<title>Trace Viewer</title>
</svelte:head>

{@render children()}
