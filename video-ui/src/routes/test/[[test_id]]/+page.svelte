<script lang="ts">
    import { onMount } from "svelte";
    import { replaceState, goto } from "$app/navigation";
    import { page } from "$app/state";
    import { resolve } from "$app/paths";

    import FileModal from "../FileModal.svelte";
	

    // let open = $state(true);

    const test_id = crypto.randomUUID();

    // Not required with goto()
    // const hasUUID = $derived.by(() => {

    //     const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

    //     const id = page.params.test_id;
    //     return id !== undefined && UUID_RE.test(id);
    // })

    // const hasUUID = $derived(!!page.params.test_id);    // The double !! is a JavaScript idiom to convert any value into a boolean.

    // let open = $state(!hasUUID);

    const open = $derived(!page.params.test_id);

    async function replaceUrl() {
        // open = false;

        // using goto() instead of replaceState because goto() is reactive, it updates page.params
        // which replaceState() doesn't
        await goto(
            resolve(`/test/${test_id}`), {
            replaceState: true,
            noScroll: true,
            keepFocus: true,
        });

        // replaceState(
        //     resolve(`/test/${test_id}`), {}
        // )
    }

    // Runs whenever the reactive values it reads change.
    // $effect(() => {
    //     open = !page.params.test_id;
    // })

</script>

<FileModal open={open} handleClick={replaceUrl} />

{#if page.params.test_id}
    <!-- URL contains a valid UUID -->
    <p>UUID is present.</p>
{:else}
    <!-- No UUID -->
    <p>UUID is NOT Present.</p>
{/if}
