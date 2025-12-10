<script lang="ts">
	import Card from '$lib/components/stats/card.svelte';
	import { animate } from 'animejs';
	import { onMount } from 'svelte';

	function animateCounter(el: HTMLElement | undefined, target: number, pad = 3) {
		if (!el) return;

		const obj = { value: 0 };

		animate(obj, {
			value: target,
			duration: 2000,
			easing: 'easeInOutSine',
			onUpdate: () => {
				el.textContent = Math.floor(obj.value).toString().padStart(pad, '0');
			}
		});
	}

	let { title, footer, number }: { title: string; footer: string; number: number } = $props();
	let element: HTMLSpanElement;
	let numberString = $derived(number?.toString().padStart(3, '0'));

	onMount(async () => {
		animateCounter(element, number, 3);
	});
</script>

<Card {title} {footer}>
	<span bind:this={element}>{numberString ?? 'Error'}</span>
</Card>
