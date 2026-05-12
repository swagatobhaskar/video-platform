<script lang="ts">

    import VideoDrop from "./VideoDrop.svelte";
    import UploadDashboard from "./UploadDashboard.svelte";
    
    import {
        createUploadWorkflowController
    } from "$lib/controllers/uploadWorkflow.svelte";

    const workflow = createUploadWorkflowController();

</script>

{#if workflow.currentStep == "video-drop"}
    <!-- <VideoDrop {workflow}/> -->
    <UploadDashboard {workflow} />
{/if}
<!-- 
{#if workflow.currentStep == "upload-dashboard"}
    <UploadDashboard {workflow} />
{/if} -->
