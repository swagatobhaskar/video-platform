<script lang="ts">
    import FolderDropZone from "./_components/FolderDropZone.svelte";
    import { UploadController } from './controller.svelte';
    const controller = UploadController();
</script>

<h1>Upload Transcoded Video</h1>

<FolderDropZone onFiles={(files) => controller.setFiles(files)} controller={controller} />

{#if controller.state.selectedFiles?.length}
    <h3>{controller.state.selectedFiles?.length} files selected.</h3>

    <button
        onclick={() => controller.upload()}
        disabled={controller.state.uploading}
    >
        Upload
    </button>
{/if}

{#if controller.state.uploading}
    <progress max="100" value={controller.state.progress}></progress>
    <p>{controller.state.progress}%</p>
{/if}

{#if controller.state.error}
    <p style="color:red">
        {controller.state.error}
    </p>
{/if}

{#if controller.state.success}
    <p style="color:green">
        {controller.state.success}
    </p>
{/if}
