<script lang="ts">
	// import { preview } from "vite";

    let isDragging = $state(false);
    let file: File | null = $state(null);
    let videoPreviewUrl: string | null = $state(null);
    let uploading: boolean = $state(false);

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

    async function uploadVideoFile(): Promise<void> {
        
        if (!file) return;
        
        // set uploading = true
        uploading = true;

        const formData = new FormData();
        formData.append("video", file);

        console.log("Inside Upload Function");
        // file = null;
        console.log("Initiate Upload Request BODY: ", JSON.stringify({ fileName: file.name, contentType: file.type }));
        // Step 1: Initiate Upload
        try {
            const res = await fetch("http://localhost:8000/api/upload/initiate-upload", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ fileName: file.name, contentType: file.type }),
            });

            const { uploadId, key } = await res.json();
            console.log("Upload ID: ", uploadId, "Key: ", key);

            if (!res.ok) {
                throw new Error("Upload failed");
        }

        console.log("Upload success");
        file = null;
        
        } catch (err) {
            console.error(err);
        } finally {
            uploading = false;
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
                                    onclick={cancelFile}
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
         <!-- Thumbnail -->
         <div class="flex-1 bg-blue-400 flex items-center justify-center">
            Box 2
         </div>
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
