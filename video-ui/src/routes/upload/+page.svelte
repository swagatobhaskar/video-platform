<script lang="ts">
    let files = $state<FileList | null>(null);
    let title = $state('');
    let uploading = $state(false);
    let message = $state("");
    let isHovered = $state(false);

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

        if (e.dataTransfer?.files) {
            files = e.dataTransfer.files;  // Assign the dropped files to our state
            console.log("Dropped file:", files[0].name);
        }
    }

    function handleMouseEnter() { isHovered = true; }
    function handleMouseLeave() { isHovered = false; }

    async function handleUpload(e: Event) {
        e.preventDefault();

        if (!files || files.length === 0) return;

        uploading = true;
        message = 'Uploading...';

        const formData = new FormData();
        formData.append("file", files[0]);
        formData.append("title", title);

        try {
            const response = await fetch("http://127.0.0.1:8000/api/upload", {
                method: "POST",
                body: formData,
                // Do NOT set Content-Type header manually; 
                // the browser sets it to multipart/form-data with the boundary automatically.
            });

            const result = await response.json();
            message = result.info || "Upload Successful!";
        } catch (error) {
            message = "Upload failed. Check Console!";
            console.error(error);
        } finally {
            uploading = false;
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
            <div class="text-center pointer-events-none">
                <span class="text-lg font-bold text-gray-700">
                    {files ? files[0].name : "Drop Video Here"}
                </span>
                <p class="text-xs text-gray-400 mt-1">or click to select from device</p>
            </div>
            <input
                bind:files
                type="file"
                accept="video/*"
                class="hidden"
            />
        </label>

        <button
            disabled={uploading}
            type="submit"
            class="bg-orange-600 text-white py-2 px-4 rounded-lg font-bold disabled:bg-gray-400 cursor-pointer"
        >
            {uploading ? "Processing..." : "Upload Video"}
        </button>
    </form>

    {#if message}
        <p class="mt-4 text-sm font-medium text-blue-600">{message}</p>
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