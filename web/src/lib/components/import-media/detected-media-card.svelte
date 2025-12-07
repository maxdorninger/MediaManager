<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';

	let {
		directory,
		isTv,
		children
	}: {
		directory: string;
		isTv: boolean;
		children: any;
	} = $props();
</script>

<Card.Root class="col-span-full flex h-full flex-col overflow-x-hidden sm:col-span-1">
	<Card.Header>
		<Card.Title class="flex h-12 items-center leading-tight">
			An importable {isTv ? 'TV show' : 'movie'} was detected!
		</Card.Title>
		<Card.Description>
			The detected {isTv ? 'TV show' : 'movie'} is in this directory:
			<code
				class="relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm font-semibold"
			>
				{directory}
			</code>
		</Card.Description>
	</Card.Header>
	<Card.Content class="flex flex-1 items-center justify-center">
		{@render children?.()}
	</Card.Content>
</Card.Root>
