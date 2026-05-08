<script lang="ts">
    import {
        createFileInputController
    } from '$lib/controllers/ui/file-input-controller.svelte';

    // Video file selection handler
    let videoFileInputEl = $state<HTMLInputElement | null>(null);

    const videoInput = createFileInputController({
        accept: [
            "video/mp4",
            "video/webm"
        ],
        maxSizeBytes: 5 * 1024 * 1024 * 1024 // 5GB
    })

    function handleFiles(files: File[]) {
        const file = files[0];
        // upload.selectFile(file);
    }

</script>

<!-- Calculating the height of this page: subtract 100vh from the header height -->

<div 
    class="h-[calc(100vh-4rem)] md:h-[calc(100vh-5rem)]
        flex items-center justify-center
    ">
    <!-- Video Drop -->
    <div class="w-screen md:w-3/5 h-4/5 md:h-3/5 bg-white rounded-4xl shadow-2xl relative">
        <!-- Inner border -->
        <div
            role="region"
            class="absolute inset-5 border-2 border-dashed border-gray-400 rounded-3xl pointer-events-none"
            ondragenter={videoInput.onDragEnter}    
            ondragleave={videoInput.onDragLeave}
            ondragover={videoInput.onDragOver}
            ondrop={videoInput.onDrop}
            class:border-blue-500={videoInput.state.isDragging}
            class:bg-blue-50={videoInput.state.isDragging}
        >
            <div class="pointer-events-auto">
                <p class="">Drag & drop or </p>
                <button type="button" onclick={videoInput.onFileSelect}>click to upload</button>
            </div>
            <input
                type="file"
                class="hidden"
                accept={videoInput.acceptAttribute}
                bind:this={videoFileInputEl}
                onchange={(e) => videoInput.onFileSelect(e)}
            />        
        </div>
    </div>
    {#if videoInput.state.error}
        <p class="error">{videoInput.state.error}</p>
    {/if}
</div>
