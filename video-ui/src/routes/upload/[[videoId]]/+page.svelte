<script lang="ts">
    
    // import { onMount } from 'svelte';
    import { page } from '$app/state';
    import { goto } from "$app/navigation";
    import { resolve } from '$app/paths';

    import VideoDropModal from '../_components/VideoDropModal.svelte';
    import FormComponent from '../_components/FormComponent.svelte';
    import ThumbnailCard from '../_components/ThumbnailCard.svelte';
    import VideoUploadProgressCard from '../_components/VideoUploadProgressCard.svelte';

    import { fileInputController } from '$lib/controllers/fileInputController.svelte';
    const videoInputController = fileInputController({uploadFileType: "video"})
    
    import { createVideoUploadSession } from '$lib/services/videoUploadSession.svelte'
    const uploader = createVideoUploadSession();

    // const videoId = $derived(!page.params.videoId);
    const videoId = $derived(page.params.videoId);
    const modalOpen = $derived(videoId === undefined);

    async function handleUploadWithNewSession() {
        // Create new upload_session and fetch the id
        try {
            const response = await fetch(
                'http://127.0.0.1:8000/api/video/uploads/new-upload-session',
                {
                    method: 'POST'
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            // remove any existing uploadSessionId, videoId from cookies
            cookieStore.delete("uploadSessionId");
            cookieStore.delete("videoId");

            // Set uploadSessionId, videoId in cookies
            cookieStore.set("uploadSessionId", data.uploadSessionId);
            cookieStore.set("videoId", data.videoId);

            // Close the modal
            // modalOpen = false;

            // Add the upload_session_id to the URL
            await goto(
                resolve(`/upload/${data.videoId}`), {
                replaceState: true,
                noScroll: true,
                keepFocus: true,
            });

            // Start the upload
            const file = videoInputController.state.selectedFile;
            
            if (file) {
                await uploader.upload(file);
            }


	    } catch (err) {
            console.error(err);
        }
    }

    // type Video = {
	// 	id: string;
	// 	title: string;
	// };
    
    let fetchedVideoData = $state(null);
    let loading = $state(false);
	let error = $state<string | null>(null);
    
    $effect(() => {
        if (!videoId) {
            fetchedVideoData = null;
            error = null;
			loading = false;
            return
        }

        const controller = new AbortController();
        loading = true;
		error = null;

        void (async () => {
            try {
                const response = await fetch(`http://127.0.0.1:8000/api/list/videos/${videoId}`);
                if (!response.ok) {
                    const errorData = await response.json();
		            throw new Error(errorData.detail ?? "Failed to fetch video"); // Following FastAPI HTTPException(detail=)
                }
                fetchedVideoData = await response.json();
            } catch (err) {
				// Ignore aborted requests
				if (err instanceof DOMException && err.name === 'AbortError') {
					return;
				}

				fetchedVideoData = null;
				error = err instanceof Error ? err.message : 'An unexpected error occurred';
			} finally {
				if (!controller.signal.aborted) {
					loading = false;
				}
			}
        })();

        return () => {
			controller.abort();
		};
    });

</script>

<!--
Why use AbortController?

Suppose the user navigates like this:

/uploads/1
→ /uploads/2
→ /uploads/3

Without aborting, the request for /1 might finish last and overwrite the data for /3.
By aborting the previous request in the effect's cleanup function, only the latest request is allowed to complete and update your state.
This avoids race conditions during rapid client-side navigation.
-->

<!-- {#if loading}
	<p>Loading...</p>
{:else if error}
	<p class="text-red-500">{error}</p>
{:else if video}
	<VideoDetails {video} />
{/if} -->

<VideoDropModal
    open={modalOpen}
    {videoInputController}
    onUploadClick={handleUploadWithNewSession}
/>

<div class="w-5/6 mx-auto h-100vh flex flex-row">
    <!-- Form Area -->
    <section class="flex-2/3">
        <!-- Form Component -->
         <!-- <FormComponent values={fetchedVideoData} /> -->
         <FormComponent />
        <!-- End of Form Component -->
    </section>
    
    <!-- Upload Progress & Thumbnail -->
    <section class="flex-1/3 flex flex-col justify-evenly">
        <!-- Upload Progress -->
        <VideoUploadProgressCard uploader={uploader} />
        
        <!-- Thumbnail -->
        <ThumbnailCard />
    </section>
</div>