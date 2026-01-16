<script lang="ts">
	import type { SpanKind } from '$lib/types';

	interface Props {
		kind: SpanKind;
	}

	let { kind }: Props = $props();

	const kindColors: Record<SpanKind, string> = {
		conversation: 'bg-purple-600',
		turn: 'bg-indigo-600',
		llm: 'bg-blue-600',
		tool: 'bg-amber-600',
		internal: 'bg-gray-600'
	};
</script>

<span
	class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium text-white {kindColors[kind]}"
>
	{kind.toUpperCase()}
</span>
