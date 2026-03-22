<script lang="ts">
	let { children } = $props();
</script>

<div class="flex flex-row">
    <aside class="w-1/4 h-full">
        <p>Sidebar</p>
    </aside>
    <main class="w-3/4">
        {@render children()}
    </main>
</div>
