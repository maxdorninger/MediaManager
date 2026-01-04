<script lang="ts">
	import X from '@lucide/svelte/icons/x';
	import Check from '@lucide/svelte/icons/check';

	let { state }: { state: boolean } = $props();
</script>

{#if state}
	<Check class="stroke-green-500" />
{:else}
	<X class="stroke-rose-600" />
{/if}
