<script lang="ts">
	import { goto } from "$app/navigation";
    import { resolve } from '$app/paths';
    
    import Modal from "./Modal.svelte";
    let { open, handleClick } = $props<{ open: boolean; handleClick: () => void; }>()
</script>

<Modal bind:open>
    <section class="">
        <p>This is a modal</p>
        <button onclick={handleClick}>Upload</button>
        <button onclick={() => goto(resolve('/'))}>Cancel</button>
    </section>
</Modal>