<script lang="ts">
    import Modal from "./_components/Modal.svelte";
    import { onMount } from 'svelte';

    let open = $state(false);

    onMount(() => {
        open = true;
    })
</script>

<!-- <buttton onclick={() => (open = true)}>
    Open Modal
</buttton> -->

<Modal bind:open>
    <h2>Hello!</h2>
    <p>This is a modal.</p>
    <button onclick={() => (open = false)}>
        Close
    </button>
</Modal>
