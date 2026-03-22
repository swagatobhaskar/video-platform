<script lang="ts">
    import Sidebar from "./Sidebar.svelte";
	let { children } = $props();
</script>

<div class="flex flex-row">
    <Sidebar />
    
    <main class="w-5/6">
        {@render children()}
    </main>
</div>
