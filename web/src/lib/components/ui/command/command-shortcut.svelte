<script lang="ts">
	import type { WithElementRef } from 'bits-ui';
	import type { HTMLAttributes } from 'svelte/elements';
	import { cn } from '$lib/utils.js';

	let {
		ref = $bindable(null),
		class: className,
		children,
		...restProps
	}: WithElementRef<HTMLAttributes<HTMLSpanElement>> = $props();
</script>

<span
	class={cn('ml-auto text-xs tracking-widest text-muted-foreground', className)}
	{...restProps}
	bind:this={ref}
>
	{@render children?.()}
</span>
