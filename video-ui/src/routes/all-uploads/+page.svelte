<script lang="ts">
    import { onMount } from "svelte";

    const filters = ['SUCCESS', 'PENDING', 'FAILED'];

    let uploads = $state();

    const fetchAllUploads = async () => {
        try {
            const response = await fetch('http://127.0.0.1:8000/api/video/uploads/list-uploads', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
            });

            if (!response.ok) {
                throw new Error();  // what?
            }

            uploads = response.json();
        } catch(err) {
            console.error(err);
        }
    };

    // fetch the upload history. success, failed, ongoig, all.
    onMount(() => {
        fetchAllUploads();
    });
</script>

<main class="">
    
</main>