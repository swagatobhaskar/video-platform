<script lang="ts">
    let files = $state<FileList | null>(null);
    let title = $state('');
    let uploading = $state(false);
    let message = $state("");
    let isHovered = $state(false);
    
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
        title = '';
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

    async function handleUpload(e: Event) {
        e.preventDefault();

        if (!files || files.length === 0) return;

        uploading = true;
        message = 'Uploading...';

        // Initialize the AbortController
        controller = new AbortController();

        const formData = new FormData();
        formData.append("file", files[0]);
        formData.append("title", title);

        try {
            const response = await fetch("http://127.0.0.1:8000/api/upload", {
                method: "POST",
                body: formData,
                signal: controller.signal  // pass the signal here

                // Do NOT set Content-Type header manually; 
                // the browser sets it to multipart/form-data with the boundary automatically.
            });

            if (!response.ok) throw new Error("Server Error");

            const result = await response.json();

            // 1. Clear the inputs/files first
            resetForm('success');
            // 2. Then set the success message (so it isn't overwritten by resetForm)
            message = result.info || "Upload Successful!";

        } catch (error: any) {
            if (error.name === 'AbortError') {
                console.log("Fetch aborted by user")
            } else {
                message = "Upload failed. Check Console!";
                console.error(error);
                uploading = false; // Ensure we re-enable the button on error
            }
        } finally {
            // We handle 'uploading = false' inside resetForm or the catch block
            controller = null;
        }
    }
</script>

<div class="p-8 max-w-lg mx-auto bg-white rounded-xl shadow-md space-y-4">
    <h1 class="text-2xl font-bold text-gray-800">Upload Video</h1>
    <form onsubmit={handleUpload} class="flex flex-col gap-4">
        <label>
            <span class="text-gray-700">Video Title</span>
            <input
                bind:value={title}
                type="text"
                placeholder="My Epic Vlog"
                class="mt-1 block w-full border rounded-md p-2"
                required
            />
        </label>

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
                        {files && files.length > 0 ? files[0].name : "Drop Video Here"}
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
                accept="video/*"
                class="hidden"
            />
        </label>

        <div class="flex gap-2">
            <button
                disabled={uploading || !files}
                type="submit"
                class="flex-1 bg-orange-600 text-white py-2 px-4 rounded-lg font-bold disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
                {uploading ? "Processing..." : "Upload Video"}
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

    {#if message}
        <p class="mt-4 text-sm font-medium {message.includes('failed') ? 'text-red-600' : 'text-green-600'}">{message}</p>
    {/if}
</div>

<style>
    .hover-pattern {
        /* Polka Dot Pattern */
        background-color: #f8fafc;
        background-image: radial-gradient(#cbd5e1 1px, transparent 1px);
        background-size: 10px 10px;
        border-color: #64748b;

        /* Zig Zag Pattern */
        /* background-color: #fffaf0;
        background-image:  
            linear-gradient(135deg, #ffedd5 25%, transparent 25%), 
            linear-gradient(225deg, #ffedd5 25%, transparent 25%), 
            linear-gradient(45deg, #ffedd5 25%, transparent 25%), 
            linear-gradient(315deg, #ffedd5 25%, transparent 25%);
        background-position:  10px 0, 10px 0, 0 0, 0 0;
        background-size: 20px 20px;
        background-repeat: repeat;
        border-color: #ea580c; */
    }
</style>