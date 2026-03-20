Since the standard `fetch` API doesn't natively support tracking upload progress, we need to use the slightly older (but very reliable) `XMLHttpRequest`. In **Svelte 5**, we can link the `progress` event directly to a `$state` variable to create a smooth, reactive UI.

Here is how to implement the progress bar with a "filling" background effect.

### 1. The Updated Script (Svelte 5)

We’ll add a `progress` state and swap `fetch` for `xhr`.

```svelte
<script lang="ts">
    let files = $state<FileList | null>(null);
    let title = $state("");
    let uploading = $state(false);
    let progress = $state(0); // 0 to 100
    let message = $state("");

    async function handleUpload(e: Event) {
        e.preventDefault();
        if (!files || files.length === 0) return;

        uploading = true;
        progress = 0;
        message = "Uploading...";

        const formData = new FormData();
        formData.append("file", files[0]);
        formData.append("title", title);

        // Using XMLHttpRequest for progress tracking
        const xhr = new XMLHttpRequest();

        // Listen for progress updates
        xhr.upload.addEventListener("progress", (event) => {
            if (event.lengthComputable) {
                progress = Math.round((event.loaded / event.total) * 100);
            }
        });

        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                const response = JSON.parse(xhr.responseText);
                message = response.info || "Upload complete!";
            } else {
                message = "Upload failed.";
            }
            uploading = false;
        };

        xhr.onerror = () => {
            message = "Network error.";
            uploading = false;
        };

        xhr.open("POST", "http://localhost:8000/upload");
        xhr.send(formData);
    }
</script>
```

---

### 2. The Visual Progress Bar (HTML/CSS)

We can make the "Zig Zag" or "Polka Dot" background actually **fill up** as the video uploads by using a CSS linear gradient that keys off the `progress` variable.

```svelte
<div class="space-y-4">
    {#if uploading}
        <div class="flex justify-between text-sm font-bold text-orange-600">
            <span>Uploading Video...</span>
            <span>{progress}%</span>
        </div>
    {/if}

    <div 
        class="relative h-12 w-full bg-gray-100 rounded-lg overflow-hidden border border-gray-200"
    >
        <div 
            class="absolute top-0 left-0 h-full transition-all duration-200 ease-out fill-pattern"
            style="width: {progress}%"
        ></div>
        
        <div class="absolute inset-0 flex items-center justify-center font-mono text-xs text-gray-700">
            {progress > 0 ? `${progress}%` : 'Waiting to start...'}
        </div>
    </div>

    <button 
        onclick={handleUpload}
        disabled={uploading || !files}
        class="w-full bg-orange-600 text-white py-3 rounded-xl font-bold active:scale-95 transition-transform disabled:bg-gray-300"
    >
        {uploading ? "Uploading..." : "Start Upload"}
    </button>
</div>

<style>
    .fill-pattern {
        background-color: #ffedd5;
        /* Zig Zag Pattern */
        background-image:  
            linear-gradient(135deg, #fb923c 25%, transparent 25%), 
            linear-gradient(225deg, #fb923c 25%, transparent 25%), 
            linear-gradient(45deg, #fb923c 25%, transparent 25%), 
            linear-gradient(315deg, #fb923c 25%, transparent 25%);
        background-position:  10px 0, 10px 0, 0 0, 0 0;
        background-size: 20px 20px;
        background-repeat: repeat;
        border-right: 2px solid #ea580c;
    }
</style>
```

---

### Key Improvements
* **Real-time Feedback:** The `progress` rune ensures the UI updates at **60fps** as the browser sends chunks of data to FastAPI.
* **Visual Interest:** Instead of a boring flat blue bar, the `fill-pattern` class uses your requested Zig Zag pattern as the "filling" mechanism. 
* **Svelte 5 Syntax:** We used `onclick={handleUpload}` instead of the old `on:click` syntax, adhering to the latest Svelte 5 event standards.

**Would you like to see how to add a "Cancel Upload" button that kills the XHR request if the user changes their mind?**