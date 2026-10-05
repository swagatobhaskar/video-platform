<script lang="ts">

    type UploadState = "idle" | "uploading" | "pausing" | "paused" | "resuming" | "cancelling" | "cancelled";

    let currState = $state<UploadState>("idle");

    // let uploading = $state(false);
    // let pausing = $state(false);
    // let paused = $state(false);
    // let resuming = $state(false);
    // let cancelling = $state(false);
    // let cancelled = $state(false);
    // let currState = $state("");

    const handlePause = () => {
        // if (cancelled || cancelling) return;
        // currState = "pausing";
        // uploading = false;
        // pausing = true;
        // paused = true;
        // pausing = false;
        // currState = "paused";

        if ( currState === 'cancelled' || currState === "cancelling" ) return;
        currState = "pausing";
        // Do async pause work here...
        currState = "paused";
    };

    const handleResume = () => {
        // if (cancelled || cancelling) return;
        // paused = false;
        // currState = "resuming";
        // resuming = true;
        // uploading = true;
        // resuming = false;
        // currState ="upload continued";

        if ( currState === 'cancelled' || currState === "cancelling" ) return;
        currState = "resuming";
        // Do async resume work here...
        currState = "uploading";
    }

    const handleCancel = () => {
        // if (cancelled || cancelling) return;
        // currState = "cancelling";
        // uploading = false;
        // paused = false;
        // cancelling = true;
        // cancelled = true;
        // cancelling = false;
        // currState = "cancelled";

        if (currState === "cancelled" || currState === "cancelling") return;
        currState = "cancelling";
        // Do async cancel work here...
        currState = "cancelled";
    };
</script>

<main class="min-h-screen flex flex-col items-center justify-center">
    <div class="flex flex-col gap-2">
        <h3>Current State: {currState}</h3>
        <button onclick={()=>currState = "uploading"}>Start</button>
    </div>

    <div class="w-64 h-32 bg-blue-500 rounded-sm">
        {#if currState === "uploading"}
            <p>Uploading...</p>
            <button onclick={handlePause}>Pause</button>
            <button onclick={handleCancel}>Cancel</button>
        {/if}

        {#if currState === "pausing"}
            <p>Pausing .../\</p>
        {/if}

        {#if currState === "paused"}
            <p>Paused /\/\/\/\</p>
            <button onclick={handleResume}>Resume</button>
            <button onclick={handleCancel}>Cancel</button>
        {/if}

        {#if currState === "resuming"}
            <p>Resuming ......</p>
        {/if}
    </div>
</main>

<style>
    button {
        padding: 2px 3px;
        background-color: rgb(181, 131, 227);
        border: blueviolet;
        border-width: 1px;
        border-radius: 10px;
    }
</style>