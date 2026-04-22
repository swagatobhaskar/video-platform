<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<header class="w-full min-h-16 md:h-20 border-b border-gray-300">
	<div class="p-6">
		<p class="font-light text-3xl text-violet-950">Cartoon Dikhao</p>
	</div>
</header>
{@render children()}
