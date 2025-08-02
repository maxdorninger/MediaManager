<script lang="ts">
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb/index.js';
	import { base } from '$app/paths';
	import logo from '$lib/images/logo.svg';
	import { PUBLIC_VERSION } from '$env/static/public';
</script>

<svelte:head>
	<title>About - MediaManager</title>
	<meta
		content="About MediaManager - Learn more about your smart PVR application"
		name="description"
	/>
</svelte:head>

<header class="flex h-16 shrink-0 items-center gap-2">
	<div class="flex items-center gap-2 px-4">
		<Sidebar.Trigger class="-ml-1" />
		<Separator class="mr-2 h-4" orientation="vertical" />
		<Breadcrumb.Root>
			<Breadcrumb.List>
				<Breadcrumb.Item class="hidden md:block">
					<Breadcrumb.Link href="{base}/dashboard">MediaManager</Breadcrumb.Link>
				</Breadcrumb.Item>
				<Breadcrumb.Separator class="hidden md:block" />
				<Breadcrumb.Item>
					<Breadcrumb.Page>About</Breadcrumb.Page>
				</Breadcrumb.Item>
			</Breadcrumb.List>
		</Breadcrumb.Root>
	</div>
</header>

<main class="mx-auto flex w-full flex-1 flex-col gap-4 items-center p-4 md:max-w-[80em]">
	<img alt="Media Manager Logo" class="mb-4 h-24 w-24" src={logo} />
	<h1 class="mb-2 text-4xl font-bold">About Media Manager</h1>
	<p class="mb-6 mt-10 max-w-2xl text-center text-lg">
		<strong>Media Manager</strong> is an all-in-one solution for organizing and building your media library.
		Built for simplicity and modernity, it helps you keep track of your favorite shows and movies and
		explore trending content—all in one place.
	</p>
	<p class="mb-2 text-sm text-muted-foreground">
		Version: v{PUBLIC_VERSION}
	</p>
	<h2
		class="mt-10 scroll-m-20 pb-2 text-3xl font-semibold tracking-tight transition-colors first:mt-0"
	>
		Made with ❤️ by Maximilian Dorninger
	</h2>
	<p class="flex flex-wrap items-center justify-center gap-4">
		<iframe
			height="225"
			src="https://github.com/sponsors/maxdorninger/card"
			style="border: 0;"
			title="Sponsor maxdorninger"
			width="600"
		></iframe>
	</p>

	<h2 class="scroll-m-20 pb-2 text-3xl font-semibold tracking-tight transition-colors first:mt-0">
		Checkout the awesome sponsors of MediaManager ❤️
	</h2>
	<div class="flex flex-wrap items-center justify-center gap-4">
		<a href="https://fosstodon.org/@aljazmerzen"
			><img alt="Aljaž Mur Eržen" src="https://github.com/aljazerzen.png" width="80px" /></a
		>&nbsp;&nbsp;
		<a href="https://github.com/ldrrp"
			><img alt="Luis Rodriguez" src="https://github.com/ldrrp.png" width="80px" /></a
		>&nbsp;&nbsp;
		<a href="https://github.com/SeimusS"
			><img alt="SeimusS" src="https://github.com/SeimusS.png" width="80px" /></a
		>&nbsp;&nbsp;
		<a href="https://github.com/brandon-dacrib"
			><img alt="Brandon P." src="https://github.com/brandon-dacrib.png" width="80px" /></a
		>&nbsp;&nbsp;
	</div>

	<h2
		class="mt-24 scroll-m-20 pb-2 text-3xl font-semibold tracking-tight transition-colors first:mt-0"
	>
		Metadata sources of MediaManager
	</h2>

	<div class="my-6 mb-6 flex items-center gap-2 text-sm text-muted-foreground sm:w-1/2 lg:w-1/3">
		<a class="flex items-center gap-2" href="https://www.themoviedb.org/" target="_blank">
			<img
				alt="TMDB Logo"
				class="h-auto w-20"
				src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_square_2-d537fb228cf3ded904ef09b136fe3fec72548ebc1fea3fbbd1ad9e36364db38b.svg"
			/>
			<span
				>Metadata provided by TMDB. Please consider adding missing information or subscribing.</span
			>
		</a>
	</div>
	<div class="my-6 mb-6 flex items-center gap-2 text-sm text-muted-foreground sm:w-1/2 lg:w-1/3">
		<a class="flex items-center gap-2" href="https://thetvdb.com/subscribe" target="_blank">
			<img
				alt="TheTVDB Logo"
				class="h-auto w-20"
				src="https://www.thetvdb.com/images/attribution/logo2.png"
			/>
			<span
				>Metadata provided by TheTVDB. Please consider adding missing information or subscribing.</span
			>
		</a>
	</div>
</main>
