<script lang="ts">
	import type { UploadController } from "../controller.svelte";

    let {
        onFiles,
        controller
    }: {
        onFiles: (files: File[]) => void,
        controller: typeof UploadController
    } = $props();

    let input: HTMLInputElement;

    function selected(e: Event) {
        const files = Array.from(
            (e.target as HTMLInputElement).files ?? []
        );

        onFiles(files)
    }

    async function dropped(e: DragEvent) {
        e.preventDefault();
        const files = Array.from(e.dataTransfer?.files ?? []);
        onFiles(files);
    }
</script>

<div
    class="dropzone"
    role="region"
    aria-label="File drop zone"
    ondragover={(e) => e.preventDefault()}
    ondrop={dropped}
>
    <p>Drop Folder Here</p>
    
    <p>or</p>

    <button onclick={() => input.click()}>
        Select Folder
    </button>

    <input
        bind:this={input}
        hidden
        type="file"
        webkitdirectory
        multiple
        onchange={selected}
    />

    {#if controller.state?.selectedFile}
        
    {/if}

</div>

<style>
    .dropzone {
        width:60%;
        margin: auto;
        border:2px dashed #888;
        border-radius:12px;
        padding:4rem;

        display:flex;
        flex-direction:column;

        align-items:center;
        justify-content:center;

        gap:1rem;
    }

    button{
        padding:.8rem 1.5rem;
    }
</style>
