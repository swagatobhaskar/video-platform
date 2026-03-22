<script lang="ts">
    let files = $state<FileList | null>(null);
    let previewUrl = $state<string | null>(null);
    let uploading = $state(false);
	let statusMessage = $state("");
    let message = $state("");
    let isHovered = $state(false);
    
    function handleFileChange(e: Event) {
        const file = (e.target as HTMLInputElement).files?.[0];
        previewUrl = file ? URL.createObjectURL(file) : null;
    }

    async function handleThumbnailUpload(e: SubmitEvent) {
        e.preventDefault();

        if (!files || files.length === 0) {
			message = "Please select an image first.";
			return;
		}

        const formData = new FormData(e.currentTarget as HTMLFormElement);
        formData.append('file', files[0]);

        uploading = true;
        statusMessage = "Uploading...";

        try {
            const response = await fetch('http://127.0.0.1:8000/api/upload/thumbnail', {
				method: 'POST',
				body: formData, // Fetch automatically sets the correct Content-Type for FormData
                // Note: Do NOT set 'Content-Type' header. 
                // The browser sets it automatically with the boundary string.
			});

			if (response.ok) {
				const result = await response.json();
				statusMessage = "Upload successful! ID: " + result.id;
			} else {
				statusMessage = "Upload failed.";
			}
		} catch (error) {
			statusMessage = "Error connecting to backend.";
		} finally {
			uploading = false;
		}    
    }
    
    // Track the controller to abort the fetch request if needed
    let controller: AbortController | null = null;

    // Add a parameter to resetForm to control the message
    function resetForm(reason: 'cancel' | 'success' | 'none' = 'none') {
        // 1. Abort the request if it's running
        if (controller) {
            controller.abort();
            controller = null;
        }

        // 2. Clear all state
        files = null;
        // title = '';
        uploading = false;
        message = 'Upload Cancelled!';
        isHovered = false;

        if (reason === 'cancel') {
            message = 'Upload cancelled!';
        } else if (reason === 'none') {
            message = "";
        }
        // Note: We don't clear message if reason is 'success' 
        // because we want the user to see the "Success!" note.
    }
    
    // Prevent the browser from opening the file
    function handleDragOver(e: DragEvent) {
        e.preventDefault();
        isHovered = true;
    }

    function handleDragLeave() {
        isHovered = false;
    }

    // Capture the files manually on drop
    function handleDrop(e: DragEvent) {
        e.preventDefault();  // Stop the video from playing
        isHovered = false;

        // 1. Extract the files from the drop event
        const droppedFiles = e.dataTransfer?.files;

        // 2. Safety Check: Ensure files exist and the list isn't empty
        if (droppedFiles && droppedFiles.length > 0) {
            files = droppedFiles;   // This updates your $state
            console.log("Dropped file:", files[0].name);
        } else {
            console.warn("No files detected in drop event.");
        }
    }

    function handleMouseEnter() { isHovered = true; }
    function handleMouseLeave() { isHovered = false; }

</script>

<div class="p-8 my-8 max-w-lg mx-auto bg-white rounded-xl shadow-md space-y-4">
    <h2 class="font-semibold text-2xl">Upload Video Thumbnail</h2>
    <form onsubmit={handleThumbnailUpload} class="flex flex-col gap-4">
        <label
            class="relative block p-6 border-2 border-dashed rounded-xl transition-all duration-300"
            class:hover-pattern={isHovered}
            onmouseenter={handleMouseEnter}
            onmouseleave={handleMouseLeave}
            ondragover={handleDragOver}
            ondragleave={handleDragLeave}
            ondrop={handleDrop}
        >
            <div class="text-center pointer-events-none flex flex-col items-center">
                <div class="flex items-center gap-2 bg-gray-50 px-3 py-1 rounded-full border border-gray-200">
                    <span class="text-lg font-bold text-gray-700">
                        {files && files.length > 0 ? files[0].name : "Drop Thumbnail Here"}
                    </span>

                    {#if files && !uploading}
                        <button
                            type="button"
                            aria-label="Remove selected file"
                            title="Remove file"
                            class="pointer-events-auto p-0.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-all"
                            onclick={(e) => {
                                e.preventDefault(); // Stop the label from opening the file picker
                                e.stopPropagation(); // Stop the event from bubbling
                                files = null;
                            }}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                        </button>
                    {/if}
                </div>
                {#if !files}
                    <p class="text-xs text-gray-400 mt-2">or click to select from device</p>
                {/if}
            </div>
            
            <input
                bind:files           
                type="file"
                accept="image/*"
                class="hidden"
            />
        </label>
        
        {#if previewUrl}
            <div class="preview">
                <img src={previewUrl} alt="preview" style="width: 200px; display: block; margin: 10px 0;" />
            </div>
        {/if}

        <div class="flex gap-2">
            <button
                disabled={uploading || !files}
                type="submit"
                class="flex-1 bg-orange-600 text-white py-2 px-4 rounded-lg font-bold disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
                {uploading ? "Processing..." : "Upload Thumbnail"}
            </button>
            
            {#if uploading}
                <button
                    onclick={() => resetForm('cancel')}
                    disabled={!files}
                    type="button"
                    class="bg-gray-200 text-gray-700 py-2 px-4 rounded-lg font-bold hover:bg-gray-300 transition-colors"
                >
                    Cancel
                </button>
            {/if}
        </div>
    </form>
    
    {#if statusMessage}
        <p class={statusMessage.includes("successful") ? "success" : "error"}>{statusMessage}</p>
    {/if}
</div>

<style>
	.preview img { max-width: 300px; margin: 1rem 0; display: block; }
	.success { color: green; }
    .hover-pattern {
        /* Polka Dot Pattern */
        background-color: #f8fafc;
        background-image: radial-gradient(#cbd5e1 1px, transparent 1px);
        background-size: 10px 10px;
        border-color: #64748b;
    }
</style>
