<script lang="ts">
	import type { HTMLAttributes } from 'svelte/elements';
	import type { WithElementRef } from 'bits-ui';
	import { cn } from '$lib/utils.js';

	let {
		ref = $bindable(null),
		class: className,
		children,
		link = false,
		...restProps
	}: WithElementRef<HTMLAttributes<HTMLTableRowElement> & { link?: boolean }> = $props();
</script>

<tr
	bind:this={ref}
	class={cn(
		'border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted',
		link && 'cursor-pointer',
		className
	)}
	{...restProps}
>
	{@render children?.()}
</tr>
