<script lang="ts">
	import { getContext } from 'svelte';
	import type { components } from '$lib/api/api';
	const user: () => components['schemas']['UserRead'] = getContext('user');
</script>

<span class="truncate font-semibold">{user().email}</span>
{#if user().is_superuser}
	<span class="truncate text-xs">Administrator</span>
{:else}
	<span class="truncate text-xs">User</span>
{/if}
