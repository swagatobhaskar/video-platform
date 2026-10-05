<script lang="ts">

    import VideoDrop from "./_components/_VideoDrop.svelte";
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

    <!-- Show video player along with metadata -->
<!-- {#if workflow.currentStep == "published"}
    <div class="h-[calc(100vh-3rem)] md:h-[calc(100vh-4rem)] flex items-center justify-center">
        <div class="bg-white rounded-xl shadow-lg p-10 text-center">
            <h2 class="text-2xl font-bold mb-4">Video Published Successfully!</h2>
            <p class="text-gray-600 mb-6">Your video has been uploaded and published.</p>
            <button
                class="bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 transition-colors duration-300"
                onclick={() => workflow.resetStep()}
            >
                Upload Another Video
            </button>
        </div>
    </div>
{/if} -->