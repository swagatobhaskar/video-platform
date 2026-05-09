<script lang="ts">
    import { formatETA, formatSpeed } from '$lib/helpers/helpers';
    import { createFileInputController } from '$lib/controllers/inputController';
    import { createVideoUploadSession } from '$lib/services/videoUploadSession.svelte';
    
    const uploader = createVideoUploadSession();

    async function uploadVideoFile() {
        if (!videoFile) return;

        uploader.upload(videoFile);

        videoFile = null;
    }

    function cancelUpload() {
        uploader.cancel();
    }

    // let videoPreviewUrl: string | null = $state(null);
    
    // let videoFile: File | null = $state<File | null>(null);
    // let isVideoDragging = $state(false);

    // File selection handler
    // let fileInputEl = $state<HTMLInputElement | null>(null);

    // const videoController = createFileInputController({
    //     accept: "video/*",

    //     onDragStateChange: (dragging) => {
    //         isVideoDragging = dragging;
    //     },

    //     onFilesSelected: ([file]) => {
    //         if (!file) return;
    //         videoFile = file;
    //         console.log("Selected video:", file.name);
    //     }
    // });

    // function openFileDialog() {
    //     fileInputEl?.click();
    // }

    function cancelVideoFile() {
        videoFile = null;

        // also reset input so same file can be re-selected
        if (fileInputEl) {
            fileInputEl.value = "";
        }
    }

    // effect for video preview
    // $effect(() => {
    //     if (!videoFile) {
    //         videoPreviewUrl = null;
    //         return;
    //     };
    //     const url = URL.createObjectURL(videoFile);
    //     videoPreviewUrl = url;
        
    //     // clean-up when file changes
    //     return () => URL.revokeObjectURL(url);
    // });

</script>

<main class="h-screen flex p-10">
    <!-- Left Column -->
     <section class="w-1/2 flex flex-col">
        <!-- Video Drop -->
         <div
            // class="my-10 mx-20 flex-1 flex items-center justify-center border-gray-400 border-2 rounded-2xl relative"
            // role="region"
            // ondragenter={videoController.handleDragEnter}
            // ondragover={videoController.handleDragOver}
            // ondragleave={videoController.handleDragLeave}
            // ondrop={videoController.handleDrop}
            // class:border-blue-500={isVideoDragging}
            // class:bg-blue-50={isVideoDragging}
        >
            <!-- <input
                type="file"
                accept="video/*"
                class="hidden"
                bind:this={fileInputEl}
                onchange={videoController.handleFileChange}
            /> -->
            <div id="inner-border" class="absolute inset-3 border-2 border-dashed border-gray-400 rounded-xl pointer-events-none">
                <div class="relative z-10 w-full h-full flex items-center justify-center text-center gap-2">
                    {#if videoFile}
                        <div class="flex flex-col items-center gap-3">

                            <!-- Video Preview -->
                            <!-- {#if videoPreviewUrl } -->
                                <!-- svelte-ignore a11y_media_has_caption -->
                                <!-- <video
                                    src={videoPreviewUrl}
                                    controls
                                    class="max-h-64 rounded-lg shadow-xl pointer-events-auto"
                                ></video>
                            {/if} -->
                            <!-- Video file name -->
                            <!-- <p class="text-gray-700">{videoFile.name}</p> -->

                            <!-- Upload & Cancel Buttons -->
                            <div class="flex gap-3 pointer-events-auto">
                                <button
                                    class="bg-gray-500 text-white py-2 px-4 rounded cursor-pointer"
                                    onclick={() => {
                                        if (uploader.uploading) cancelUpload();
                                        else cancelVideoFile();
                                    }}
                                >
                                    Cancel
                                </button>
                                <button
                                    class="bg-blue-500 text-white py-2 px-4 rounded cursor-pointer"
                                    onclick={uploadVideoFile}
                                >
                                    { uploader.uploading ? 'Uploading...' : 'Upload' }
                                </button>
                            </div>
                        </div>
                    {:else}
                        <!-- <p class="text-2xl text-gray-700">Drag and drop your video here or</p>
                        <div class="flex items-center gap-2">            
                            <button
                                class="bg-blue-500 text-white py-2 px-4 rounded pointer-events-auto cursor-pointer"
                                onclick={openFileDialog}    
                            >
                                Click
                            </button>
                            <p class="text-2xl text-gray-700">to select</p>
                        </div> -->
                    {/if}
                </div>
            </div>
         </div>
         <!-- Video Upload Progress -->
         {#if uploader.uploading}
             <div class="w-full bg-gray-200 rounded-full h-2.5 mb-2">
                 <div class="bg-blue-500 h-2.5 rounded-full" style="width: {uploader.progress}%" ></div>
                 <p>Progress: {uploader.progress}%</p>
                 <p>Speed: {formatSpeed(uploader.speed)}</p>
                 <p>ETA: {formatETA(uploader.eta)}</p>
             </div>
         {/if}
         {#if uploader.error}
             <p class="text-red-500 mt-2">{uploader.error}</p>
         {/if}

         <!-- Thumbnail -->
         <!-- <div class="flex-1 bg-blue-400 flex items-center justify-center">
            Box 2
         </div> -->
     </section>

     <!-- Right Column -- Form -->
    <!-- <section class="w-1/2 flex items-center justify-center">
        <form class="w-3/4">
            <h2 class="text-xl mb-4">Video Details </h2>
            <label class="" for="title">Title</label>
            <input class="w-full mb-2 p-2 border" id="title" placeholder="Title" type="text" />            
            <label class="" for="description">Description</label>
            <input class="w-full mb-2 p-2 border" id="description" placeholder="Description" type="text" />
            <button type="submit" class="w-full bg-blue-500 text-white p-2">Submit</button>
        </form>
    </section> -->
</main>
