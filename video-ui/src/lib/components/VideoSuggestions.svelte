<!-- Placeholder for random suggestions. Replace the loop with real cards later. -->
<script lang="ts">
	let { count = 5 }: { count?: number } = $props();
</script>
 
<aside aria-label="Suggested videos">
	<h2 class="mb-3 text-sm font-semibold text-neutral-900">Suggested</h2>
	<ul class="flex flex-col gap-5">
		{#each Array(count) as _, i (i)}
			<li class="flex gap-3">
				<div class="aspect-video w-56 shrink-0 rounded bg-neutral-200"></div>
				<div class="flex min-w-0 flex-1 flex-col gap-3 pt-2">
					<div class="h-3 w-full rounded-sm bg-neutral-200"></div>
					<div class="h-3 w-3/4 rounded-sm bg-neutral-200"></div>
					<div class="h-2.5 w-1/2 rounded-sm bg-neutral-100"></div>
				</div>
			</li>
		{/each}
	</ul>
</aside>
 