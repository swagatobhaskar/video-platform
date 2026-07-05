<script lang="ts">
    // import { onMount } from 'svelte';
    
    let {
        open = $bindable(false),
        children
    } = $props();
    
    // onMount(() => {
    // Don't close modal on Escape press
    //     function handleKeyDown(e: KeyboardEvent) {
    //         if (e.key === 'Escape') {
    //             open = false;
    //         }
    //     }
    //     window.addEventListener('keydown', handleKeyDown);
    //     return () => {
    //         window.removeEventListener('keydown', handleKeyDown);
    //     };
    // });
</script>


{#if open}
    <div
        class="backdrop"
        // onclick={() => (open=false)}   // Don't close modal on backdrop click
    >
        <div
            class="modal"
            role="dialog"
            aria-modal="true"
            // aria-labelledby=""
            tabindex="-1"
            // onclick={(e) => e.stopPropagation()}  // Not required since backdrop no longer has click event
        >
            {@render children?.()}
        </div>
    </div>
{/if}

<style>
    .backdrop {
        position: fixed;
        inset: 0;
        background: rgb(0 0 0 / 0.5);
        display: grid;
        place-items: center;
    }

    .modal {
        background: white;
        padding: 2rem;
        border-radius: 0.5rem;
        min-width: 20rem;
        max-width: 40rem;
    }
</style>
