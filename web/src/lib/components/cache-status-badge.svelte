<script lang="ts">
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { LoaderCircle, Zap, Clock } from 'lucide-svelte';
	import client from '$lib/api';

	let { infoHash } = $props<{ infoHash: string | null }>();
	
	let cacheStatus: 'loading' | 'cached_torbox' | 'cached_realdebrid' | 'not_cached' | 'error' | 'no_hash' = $state('loading');
	let abortController: AbortController | null = null;

	async function checkCache(signal: AbortSignal) {
		if (!infoHash) {
			cacheStatus = 'no_hash';
			return;
		}

		try {
			const { data, response } = await client.GET('/api/v1/debrid/cache', {
				params: { query: { hash: infoHash } },
				signal
			});

			if (signal.aborted) return;

			if (!response.ok) {
				cacheStatus = 'no_hash';
				return;
			}

			if (data?.is_cached) {
				if (data.provider === 'torbox') {
					cacheStatus = 'cached_torbox';
				} else if (data.provider === 'realdebrid') {
					cacheStatus = 'cached_realdebrid';
				} else {
					cacheStatus = 'cached_torbox';
				}
			} else {
				cacheStatus = 'not_cached';
			}
		} catch (e) {
			if (e instanceof DOMException && e.name === 'AbortError') return;
			console.error('Cache check failed:', e);
			cacheStatus = 'no_hash';
		}
	}

	$effect(() => {
		if (infoHash) {
			abortController?.abort();
			abortController = new AbortController();
			
			cacheStatus = 'loading';
			checkCache(abortController.signal);
		} else {
			cacheStatus = 'no_hash';
		}

		return () => {
			abortController?.abort();
		};
	});
</script>

{#if cacheStatus === 'loading'}
	<Badge variant="outline" class="gap-1 text-muted-foreground">
		<LoaderCircle class="h-3 w-3 animate-spin" />
	</Badge>
{:else if cacheStatus === 'cached_torbox'}
	<Badge class="gap-1 bg-emerald-500 hover:bg-emerald-600 text-white">
		<Zap class="h-3 w-3" />
		Instant
	</Badge>
{:else if cacheStatus === 'cached_realdebrid'}
	<Badge class="gap-1 bg-blue-500 hover:bg-blue-600 text-white">
		<Zap class="h-3 w-3" />
		Instant
	</Badge>
{:else if cacheStatus === 'not_cached'}
	<Badge variant="outline" class="gap-1 text-amber-600 border-amber-500">
		<Clock class="h-3 w-3" />
		Slow
	</Badge>
{/if}

