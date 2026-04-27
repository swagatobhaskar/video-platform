<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';

	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	let { children } = $props();

	const isActive = (path: string) => page.url.pathname === path;
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<header class="w-full min-h-16 md:h-20 border-b border-gray-300">
	<div class="w-5/6 flex flex-row justify-between items-center">
		<div class="p-6">
			<p class="font-light text-4xl font-serif text-violet-950">Upload & Scram</p>
		</div>
		<!-- Menu Buttons -->
		<nav class="">
			{#if isActive('/upload')}
				<span class="disabled text-gray-700">New Upload</span>
			{:else}
				<a
					href={resolve('/upload')}
					class="hover:text-violet-700 text-lg"
				>
					New Upload
				</a>
			{/if}
		</nav>
	</div>
</header>

{@render children()}
