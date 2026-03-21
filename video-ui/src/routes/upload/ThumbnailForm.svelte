<script lang="ts">
    let previewUrl = $state<string | null>(null);
    let uploading = $state(false);
	let statusMessage = $state("");
    
    function handleFileChange(e: Event) {
        const file = (e.target as HTMLInputElement).files?.[0];
        previewUrl = file ? URL.createObjectURL(file) : null;
    }

    async function handleThumbnailUpload(e: SubmitEvent) {
        e.preventDefault();
        const formData = new FormData(e.currentTarget as HTMLFormElement);

        uploading = true;
        statusMessage = "Uploading...";

        try {
            const response = await fetch('http://your-fastapi-url.com/upload', {
				method: 'POST',
				body: formData, // Fetch automatically sets the correct Content-Type for FormData
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

</script>

<div class="">
    <h2 class="">Upload Video Thumbnail</h2>
    <form onsubmit={handleThumbnailUpload}>
        <input
            type="file"
            name="image"
            accept="image/*"
            onchange={handleFileChange}
            required
        />
        
        {#if previewUrl}
            <div class="preview">
                <img src={previewUrl} alt="preview" style="width: 200px; display: block; margin: 10px 0;" />
            </div>
        {/if}

        <button type="submit" disabled={uploading}>
		    {uploading ? "Uploading..." : "Upload Thumbnail"}
	    </button>
    </form>
    
    {#if statusMessage}
        <p class={statusMessage.includes("successful") ? "success" : "error"}>{statusMessage}</p>
    {/if}
</div>

<style>
	.preview img { max-width: 300px; margin: 1rem 0; display: block; }
	.success { color: green; }
</style>