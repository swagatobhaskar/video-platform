<script lang="ts">

    import VideoDrop from "./VideoDrop.svelte";
    
    import {
        createUploadWorkflowController
    } from "$lib/controllers/uploadWorkflow.svelte";

    const workflow = createUploadWorkflowController();
 
</script>

{#if workflow.currentStep == "idle"}
    <VideoDrop />
{/if}




