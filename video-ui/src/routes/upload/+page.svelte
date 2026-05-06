<script lang="ts">
    import {
        splitFileIntoChunks,
        formatSpeed,
        formatETA,
        uploadChunkWithProgress
    } from './helpers';

    // let isDragging = $state(false);
    let file: File | null = $state(null);
    let videoPreviewUrl: string | null = $state(null);
    let uploading: boolean = $state(false);
    let uploadProgress: number = $state(0);
    let error: string | null = $state(null);

    let totalUploadedBytes = 0;
    let startTime = Date.now();
    let uploadSpeed = $state(0);  // bytes per second
    let uploadETA = $state(0);  // seconds remaining

    let abortController: AbortController | null = null;
    let activeXHR: XMLHttpRequest | null = null;

    // GLOBAL upload session tracking
    let currentUploadId: string | null = null;
    let currentKey: string | null = null;

    // ---------------- File Input ----------------
    import { createFileInputController } from '$lib/controller/inputController';
    let videoFile: File | null = $state<File | null>(null);
    let isVideoDragging = $state(false);

    // File selection handler
    let fileInputEl = $state<HTMLInputElement | null>(null);

    const videoController = createFileInputController({
        accept: "video/*",

        onDragStateChange: (dragging) => {
            isVideoDragging = dragging;
        },

        onFilesSelected: ([file]) => {
            if (!file) return;
            videoFile = file;
            console.log("Selected video:", file.name);
        }
    });

    function openFileDialog() {
        fileInputEl?.click();
    }

    function cancelVideoFile() {
        videoFile = null;

        // also reset input so same file can be re-selected
        if (fileInputEl) {
            fileInputEl.value = "";
        }
    }

    async function uploadVideoFile(): Promise<void> {
        if (!videoFile) return;
        const currentVideoFile = videoFile; // stable reference

        uploading = true;
        uploadProgress = 0;
        error = null;

        abortController = new AbortController();
        const signal = abortController.signal;

        // reset timing each upload
        startTime = Date.now();
        totalUploadedBytes = 0;

        try {
            // STEP 1: Initiate Upload
            const res = await fetch("http://localhost:8000/api/upload/initiate-upload", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    fileName: currentVideoFile.name,
                    contentType: currentVideoFile.type
                }),
                signal
            });
            
            if (!res.ok) {
                throw new Error(`Upload Initiation Failed: ${res.status}`);
            }
            
            const { uploadId, key } = await res.json();
            
            // store globally for cancel access
            currentUploadId = uploadId;
            currentKey = key;
            
            const chunks = splitFileIntoChunks(currentVideoFile);
            const parts: { ETag: string | null; PartNumber: number }[] = [];
        
            // STEP 2-3: Upload Chunks
            for (let i=0; i < chunks.length; i++) {
                const partNumber = i + 1;

                // Get Presigned URL
                console.log("Entering step 2 for part number: ", partNumber);
                const urlRes = await fetch(
                    "http://127.0.0.1:8000/api/upload/get-presigned-url",
                    {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ uploadId, key, partNumber }),
                        signal
                    }
                );

                if (!urlRes.ok) {
                    throw new Error(`Failed to get URL for part ${partNumber}`);
                }

                const {uploadUrl} = await urlRes.json();

                // Step 3: Upload chunk directly to R2
                console.log("Entering step 3 for part number: ", partNumber);

                if (!uploadUrl) {
                    throw new Error(`Missing upload URL for part ${partNumber}`);
                }

                // Upload Chunk
                let previousLoaded = 0;

                const { etag } = await uploadChunkWithProgress(
                    uploadUrl,
                    chunks[i],
                    (loaded) => {
                        // Increment only the delta
                        const delta = loaded - previousLoaded;
                        previousLoaded = loaded;

                        totalUploadedBytes += delta;

                        const elapsedSeconds = (Date.now() - startTime) / 1000;

                        // Speed (bytes/seconds)
                        uploadSpeed = totalUploadedBytes / elapsedSeconds;

                        // ETA (seconds)
                        const remainingBytes = currentVideoFile.size - totalUploadedBytes;
                        uploadETA = remainingBytes / uploadSpeed;

                        // Progress %
                        uploadProgress = Math.round(
                            (totalUploadedBytes / currentVideoFile.size) * 100
                        );
                    },
                    signal
                );

                // const etag = uploadRes.headers.get("ETag");

                console.log(`Uploaded part ${partNumber}, ETag: ${etag}`);

                parts.push({
                    ETag: etag,
                    PartNumber: partNumber
                });
            }

            // Step 4: Complete Upload
            console.log("Entering step 4 to complete upload");
            const completeRes = await fetch(
                "http://127.0.0.1:8000/api/upload/complete-upload",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        key,
                        filename: currentVideoFile.name,
                        uploadId,
                        parts
                    }),
                    signal
                }
            );

            if (!completeRes.ok) {
                throw new Error("Failed to complete upload");
            }
            
            console.log("Upload success");
            videoFile = null;
        
        } catch (err: unknown) {
            if (err instanceof Error) {
                if (err.message === "Upload Cancelled") {
                    console.log("Upload cancelled by user");
                } else if (err.name === "AbortError") {
                    console.log("Fetch Aborted");
                } else {
                    error = err.message;
                    console.error(err.message);
                }
            } else {
                error = "An unknown error occurred during upload.";
                console.error(error);
            }
        } finally {
            uploading = false;
            
            // cleanup session
            currentUploadId = null;
            currentKey = null;
        }
    }

    // ---------------- Cancel Upload ----------------
    
    async function cancelVideoUpload() {
        // abort all fetch requests
        abortController?.abort();
        // abort current XHR if running
        activeXHR?.abort();

        try {
            // Only call if XHR started
            if (currentUploadId && currentKey) {
                await fetch("http://127.0.0.1:8000/api/upload/abort-upload", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        uploadId: currentUploadId,
                        key: currentKey
                    })
                });
            }
        } catch (e) {
            console.warn("Abort cleanup failed", e)
        }

        // Reset controllers and trackers
        abortController = null;
        activeXHR = null;

        // Reset upload session tracking
        currentUploadId = null;
        currentKey = null;

        // Reset state
        uploading = false;
        uploadProgress = 0;
        uploadSpeed = 0;
        uploadETA = 0;
        totalUploadedBytes = 0;

        videoFile = null;

        if (fileInputEl) {
            fileInputEl.value = "";
        }
    }

    // effect for video preview
    $effect(() => {
        if (!videoFile) {
            videoPreviewUrl = null;
            return;
        };
        const url = URL.createObjectURL(videoFile);
        videoPreviewUrl = url;
        
        // clean-up when file changes
        return () => URL.revokeObjectURL(url);
    });

</script>

<main class="h-screen flex p-10">
    <!-- Left Column -->
     <section class="w-1/2 flex flex-col">
        <!-- Video Drop -->
         <div
            class="my-10 mx-20 flex-1 flex items-center justify-center border-gray-400 border-2 rounded-2xl relative"
            role="region"
            ondragenter={videoController.handleDragEnter}
            ondragover={videoController.handleDragOver}
            ondragleave={videoController.handleDragLeave}
            ondrop={videoController.handleDrop}
            class:border-blue-500={isVideoDragging}
            class:bg-blue-50={isVideoDragging}
        >
            <input
                type="file"
                accept="video/*"
                class="hidden"
                bind:this={fileInputEl}
                onchange={videoController.handleFileChange}
            />
            <div id="inner-border" class="absolute inset-3 border-2 border-dashed border-gray-400 rounded-xl pointer-events-none">
                <div class="relative z-10 w-full h-full flex items-center justify-center text-center gap-2">
                    {#if videoFile}
                        <div class="flex flex-col items-center gap-3">

                            <!-- Video Preview -->
                            {#if videoPreviewUrl }
                                <!-- svelte-ignore a11y_media_has_caption -->
                                <video
                                    src={videoPreviewUrl}
                                    controls
                                    class="max-h-64 rounded-lg shadow-xl pointer-events-auto"
                                ></video>
                            {/if}
                            <!-- Video file name -->
                            <p class="text-gray-700">{videoFile.name}</p>

                            <!-- Upload & Cancel Buttons -->
                            <div class="flex gap-3 pointer-events-auto">
                                <button
                                    class="bg-gray-500 text-white py-2 px-4 rounded cursor-pointer"
                                    onclick={ uploading ? cancelVideoUpload : cancelVideoFile}
                                >
                                    Cancel
                                </button>
                                <button
                                    class="bg-blue-500 text-white py-2 px-4 rounded cursor-pointer"
                                    onclick={uploadVideoFile}
                                >
                                    { uploading ? 'Uploading...' : 'Upload' }
                                </button>
                            </div>
                        </div>
                    {:else}
                        <p class="text-2xl text-gray-700">Drag and drop your video here or</p>
                        <div class="flex items-center gap-2">            
                            <button
                                class="bg-blue-500 text-white py-2 px-4 rounded pointer-events-auto cursor-pointer"
                                onclick={openFileDialog}    
                            >
                                Click
                            </button>
                            <p class="text-2xl text-gray-700">to select</p>
                        </div>
                    {/if}
                </div>
            </div>
         </div>
         <!-- Video Upload Progress -->
         {#if uploading}
             <div class="w-full bg-gray-200 rounded-full h-2.5 mb-2">
                 <div class="bg-blue-500 h-2.5 rounded-full" style="width: {uploadProgress}%" ></div>
                 <p>Progress: {uploadProgress}%</p>
                 <p>Speed: {formatSpeed(uploadSpeed)}</p>
                 <p>ETA: {formatETA(uploadETA)}</p>
             </div>
         {/if}
         {#if error}
             <p class="text-red-500 mt-2">{error}</p>
         {/if}

         <!-- Thumbnail -->
         <!-- <div class="flex-1 bg-blue-400 flex items-center justify-center">
            Box 2
         </div> -->
     </section>

     <!-- Right Column -- Form -->
    <section class="w-1/2 flex items-center justify-center">
        <form class="w-3/4">
            <h2 class="text-xl mb-4">Video Details </h2>
            <label class="" for="title">Title</label>
            <input class="w-full mb-2 p-2 border" id="title" placeholder="Title" type="text" />            
            <label class="" for="description">Description</label>
            <input class="w-full mb-2 p-2 border" id="description" placeholder="Description" type="text" />
            <button type="submit" class="w-full bg-blue-500 text-white p-2">Submit</button>
        </form>
    </section>
</main>
