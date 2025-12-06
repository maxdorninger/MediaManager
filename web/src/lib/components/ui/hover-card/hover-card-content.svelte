<script lang="ts">
	import { LinkPreview as HoverCardPrimitive } from 'bits-ui';
	import { cn } from '$lib/utils.js';

	let {
		ref = $bindable(null),
		class: className,
		align = 'center',
		sideOffset = 4,
		portalProps,
		...restProps
	}: HoverCardPrimitive.ContentProps & {
		portalProps?: HoverCardPrimitive.PortalProps;
	} = $props();
</script>

<HoverCardPrimitive.Portal {...portalProps}>
	<HoverCardPrimitive.Content
		bind:ref
		{sideOffset}
		{align}
		class={cn(
			'z-50 w-64 rounded-md border bg-popover p-4 text-popover-foreground shadow-md outline-none',
			className
		)}
		{...restProps}
	/>
</HoverCardPrimitive.Portal>
