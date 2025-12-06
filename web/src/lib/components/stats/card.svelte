<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';

	// eslint-disable-next-line
	let { title, footer, children }: { title: string; footer: string; children: any } = $props();
</script>

<Card.Root>
	<Card.Header>
		<Card.Title><p>{title}</p></Card.Title>
	</Card.Header>
	<Card.Content>
		<p class="text-3xl font-extrabold">{@render children?.()}</p>
	</Card.Content>
	<Card.Footer>
		<Card.Description>
			<p>{footer}</p>
		</Card.Description>
	</Card.Footer>
</Card.Root>
