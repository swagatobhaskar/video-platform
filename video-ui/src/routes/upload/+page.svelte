<script lang="ts">
	import { sign } from "crypto";

	// import { preview } from "vite";

    let isDragging = $state(false);
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

    // Drag events and handlers
    function handleDragEnter(e: DragEvent) {
        e.preventDefault();
        isDragging = true;
    }

    function handleDragOver(e: DragEvent) {
        e.preventDefault();
    }

    function handleDragLeave() {
        isDragging = false;
    }

    function handleDrop(e: DragEvent) {
        e.preventDefault();
        isDragging = false;

        const files = e.dataTransfer?.files;
        if (files && files.length > 0) {
            file = files[0];
            console.log("Dropped file: ", file);
        }
    }

    // File selection handler
    let fileInputEl = $state<HTMLInputElement | null>(null);

    function openFileDialog() {
        fileInputEl?.click();
    }

    function handleFileChange(e: Event) {
        const target = e.target as HTMLInputElement;
        if (target.files?.length) {
            file = target.files[0];
        }
    }

    function cancelFile() {
        file = null;

        // also reset input so same file can be re-selected
        if (fileInputEl) {
            fileInputEl.value = "";
        }
    }

    function splitFileIntoChunks(file: File, chunkSizeMB: number = 5): Blob[] {
        const chunkSize = chunkSizeMB * 1024 * 1024; // Convert MB to bytes
        const chunks: Blob[] = [];
        let offset = 0;

        while (offset < file.size) {
            const chunk = file.slice(offset, offset + chunkSize);
            chunks.push(chunk);
            offset += chunkSize;
        }

        return chunks;
    }

    function formatSpeed(bytesPerSec: number): string {
        if (bytesPerSec < 1024) return `${bytesPerSec.toFixed(0)} B/s`;
        if (bytesPerSec < 1024 * 1024) {
            return `${(bytesPerSec / 1024).toFixed(1)} KB/s`;
        }

        return `${(bytesPerSec / (1024 * 1024)).toFixed(1)} MB/s`;
    }

    function formatETA(seconds: number): string {
        if (!isFinite(seconds)) return "Calculating...";
        if (seconds < 60) return `${Math.ceil(seconds)}s`;

        const min = Math.floor(seconds / 60);
        const sec = Math.ceil(seconds % 60);
        return `${min}m ${sec}s`;
    }

    function uploadChunkWithProgress(
        url: string,
        chunk: Blob,
        onProgress: ( loaded: number, total: number ) => void,
        signal: AbortSignal
    ): Promise<{ etag: string | null }> {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            activeXHR = xhr;  // track current XHR

            xhr.open("PUT", url, true);

            xhr.upload.onprogress = (event) => {
                if (event.lengthComputable) {
                    // const percent = (event.loaded / event.total) * 100;
                    onProgress(event.loaded, event.total);
                }
            };

            xhr.onload = () => {
                activeXHR = null;
                if (xhr.status >= 200 && xhr.status < 300) {
                    const etag = xhr.getResponseHeader("ETag");
                    resolve({ etag });
                } else {
                    reject(new Error(`XHR upload failed: ${xhr.status}`));
                }
            };

            xhr.onabort = () => {
                activeXHR = null;
                reject(new Error("Upload Cancelled"));
            };

            xhr.onerror = () => {
                activeXHR = null;
                reject(new Error("XHR network error"));
            };

            // Link AbortController --> XHR
            signal.addEventListener("abort", () => {
                xhr.abort();
            });

            xhr.send(chunk);
        });
    }


    async function uploadVideoFile(): Promise<void> {
        if (!file) return;
        const currentFile = file; // stable reference

        uploading = true;
        uploadProgress = 0;
        error = null;

        abortController = new AbortController();
        const signal = abortController.signal;

        try {
            // STEP 1: Initiate Upload
            const res = await fetch("http://localhost:8000/api/upload/initiate-upload", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    fileName: currentFile.name,
                    contentType: currentFile.type
                }),
                signal
            });
            
            if (!res.ok) {
                throw new Error(`Upload Initiation Failed: ${res.status}`);
            }
            
            const { uploadId, key } = await res.json();
            
            const chunks = splitFileIntoChunks(currentFile);
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
                
                // const uploadRes = await fetch(uploadUrl, {
                //     method: "PUT",
                //     body: chunks[i]
                // });

                // const chunkIndex = i;
                let previousLoaded = 0;

                const { etag } = await uploadChunkWithProgress(
                    uploadUrl,
                    chunks[i],
                    (loaded, _total) => {
                        // Combine chunk progress + completed chunks
                        // const overall = ((chunkIndex + chunkPercent / 100) / chunks.length) * 100;
                        // uploadProgress = Math.round(overall);

                        // Increment only the delta
                        const delta = loaded - previousLoaded;
                        previousLoaded = loaded;

                        totalUploadedBytes += delta;

                        const elapsedSeconds = (Date.now() - startTime) / 1000;

                        // Speed (bytes/seconds)
                        uploadSpeed = totalUploadedBytes / elapsedSeconds;

                        // ETA (seconds)
                        const remainingBytes = currentFile.size - totalUploadedBytes;
                        uploadETA = remainingBytes / uploadSpeed;

                        // Progress %
                        uploadProgress = Math.round(
                            (totalUploadedBytes / currentFile.size) * 100
                        );
                    },
                    signal
                );

                // if (!uploadRes.ok) {
                //     throw new Error(`Upload failed for part ${partNumber}`);
                // }

                // const etag = uploadRes.headers.get("ETag");

                console.log(`Uploaded part ${partNumber}, ETag: ${etag}`);

                parts.push({
                    ETag: etag,
                    PartNumber: partNumber
                });  // this needs to be sent to backend as well

                // Update Progress
                // uploadProgress = Math.round(((i + 1) / chunks.length) * 100);
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
                        filename: currentFile.name,
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
            file = null;
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
        }
    }

    function cancelUpload() {
        // abort all fetch requests
        abortController?.abort();
        abortController = null;

        // abort current XHR if running
        activeXHR?.abort();
        activeXHR = null;

        // Reset state
        uploading = false;
        uploadProgress = 0;
        uploadSpeed = 0;
        uploadETA = 0;
        totalUploadedBytes = 0;

        file = null;

        if (fileInputEl) {
            fileInputEl.value = "";
        }
    }

    // effect for video preview
    $effect(() => {
        if (!file) return;
        
        const url = URL.createObjectURL(file);
        console.log("Inside effect, video url: ", url);
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
            // ARIA role
            role="region"
            // Apply the drag event handlers
            ondragenter={handleDragEnter}
            ondragover={handleDragOver}
            ondragleave={handleDragLeave}
            ondrop={handleDrop}
            // Add conditional visual cues
            class:border-blue-500={isDragging}
            class:bg-blue-50={isDragging}
        >
            <input
                type="file"
                accept="video/*"
                class="hidden"
                bind:this={fileInputEl}
                onchange={handleFileChange}
            />
            <div id="inner-border" class="absolute inset-3 border-2 border-dashed border-gray-400 rounded-xl pointer-events-none">
                <div class="relative z-10 w-full h-full flex items-center justify-center text-center gap-2">
                    {#if file}
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
                            <p class="text-gray-700">{file.name}</p>

                            <!-- Upload & Cancel Buttons -->
                            <div class="flex gap-3 pointer-events-auto">
                                <button
                                    class="bg-gray-500 text-white py-2 px-4 rounded cursor-pointer"
                                    onclick={ uploading ? cancelUpload : cancelFile}
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
