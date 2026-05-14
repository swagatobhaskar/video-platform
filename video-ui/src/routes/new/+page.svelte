<script lang="ts">

    import VideoDrop from "./_components/VideoDrop.svelte";
    import UploadDashboard from "./_components/UploadDashboard.svelte";
    
    import {
        createUploadWorkflowController
    } from "$lib/controllers/uploadWorkflow.svelte";

    const workflow = createUploadWorkflowController();

</script>

{#if workflow.currentStep == "video-drop"}
    <VideoDrop {workflow}/>
{/if}

{#if workflow.currentStep == "upload-dashboard"}
    <UploadDashboard {workflow} />
{/if}
