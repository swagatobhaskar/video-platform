<script lang="ts">

	import { page } from '$app/state';
	import { resolve } from '$app/paths';

	const isActive = (path: string) => page.url.pathname === path;
</script>

<header class="w-full min-h-16 md:h-20 border-b border-gray-300">
	<div class="w-5/6 flex flex-row justify-between items-center">
		<div class="p-6">
			<a
                href={resolve('/')}
                class="inline-block text-4xl font-semibold font-sans tracking-wider bg-linear-to-r
                from-blue-700 via-indigo-600 to-fuchsia-900 bg-clip-text text-transparent">
                Cartoon Dikhao
            </a>
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