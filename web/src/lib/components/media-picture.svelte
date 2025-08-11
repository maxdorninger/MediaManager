<script>
	import { getFullyQualifiedMediaName } from '$lib/utils.js';
	import { env } from '$env/dynamic/public';

	const apiUrl = env.PUBLIC_API_URL;
	let { media } = $props();
	console.log('got media: ', media);
</script>

<picture>
	<source srcset="{apiUrl}/static/image/{media.id}.avif" type="image/avif" />
	<source srcset="{apiUrl}/static/image/{media.id}.webp" type="image/webp" />
	<img
		alt="{getFullyQualifiedMediaName(media)}'s Poster Image"
		class="h-full w-full rounded-lg object-cover"
		src="{apiUrl}/static/image/{media.id}.jpeg"
	/>
</picture>
