<script lang="ts">

    import { createTranscodedFolderUploader, type UploadFile } from '$lib/services/transcodedFolderUploader.svelte'

    let { uploader } = $props<{ uploader: ReturnType<typeof createTranscodedFolderUploader>; }>();

    // import { formatETA, formatSpeed } from '$lib/helpers/multipartUploadHelper';
	// import UploadProgressSkleton from "$lib/components/ui/uploadProgressSkleton.svelte";
	import UploadCompleteBar from "$lib/components/ui/uploadCompleteBar.svelte";

    function handlePauseUpload() {
        uploader.pause();
    }

    function handleResumeUpload() {
        uploader.resume();
    }

    function cancelUpload() {
        // show alert
        const confirmed = confirm("Are you sure you want to cancel the upload?");
        if (!confirmed) return; // User chose No, keep uploading
        uploader.cancel();
    }

    function formatSpeed(bytesPerSec: number): string {
        if (!bytesPerSec || bytesPerSec <= 0) return "-";
        const units = ["B/s", "KB/s", "MB/s", "GB/s"];
        let value = bytesPerSec;
        let unitIndex= 0;
        while (value >= 1024 && unitIndex < units.length - 1) {
            value /= 1024;
            unitIndex++;
        }
        return `${value.toFixed(value < 10 ? 1 : 0)} ${units[unitIndex]}`;
    }

    function formatETA(seconds: number | null): string {
        if (seconds === null || !Number.isFinite(seconds)) return "unknown";
        if (seconds < 60) return `${Math.ceil(seconds)}s`;
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.round(seconds % 60);
        if (minutes < 60) return `${minutes}m ${remainingSeconds}s`;
        const hours = Math.floor(minutes / 60);
        return `${hours}h ${minutes % 60}m`;
    }

    // Bounded by `concurrency` (default 6) -- safe to render live, however many
    // hundreds of files are in the batch overall.
    let uploadingFiles = $derived(uploader.state.files.filter((f: UploadFile) => f.status === "uploading"));  // any -> UploadFile
 
    // Usually empty or tiny; worth always showing in full so errors aren't buried.
    let failedFiles = $derived(uploader.state.files.filter((f: UploadFile) => f.status === "failed"));
 
    let pendingCount = $derived(
        uploader.state.files.filter((f: UploadFile) => f.status === "pending" || f.status === "presigning").length,
    );
 
    // The full per-file list is the expensive one with hundreds of files --
    // only mount it when the user actually asks to see it.
    let showAllFiles = $state(false);
</script>

<div class="h-80 relative overflow-hidden border border-gray-200 p-6">
    {#if uploader.state.status === "uploading" || uploader.state.status === "paused"}
        {@const isPaused = uploader.state.status === "paused"}
 
        <div class="space-y-5">
            <!-- LIVE STATUS -->
            <div class="flex items-center gap-3">
                <div class="relative">
                    <div class="h-3 w-3 rounded-full {isPaused ? 'bg-yellow-500' : 'bg-green-500'}"></div>
                    {#if !isPaused}
                        <div class="absolute inset-0 animate-ping rounded-full bg-green-400"></div>
                    {/if}
                </div>
                <p class="text-sm font-medium text-gray-600">
                    {isPaused ? "Upload paused" : "Uploading…"}
                </p>
            </div>
 
            <!-- Header -->
            <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                    <h3 class="truncate font-semibold text-gray-900 text-lg">
                        {uploader.uploadedFileCount}/{uploader.state.files.length} files
                    </h3>
                </div>
 
                <div class="shrink-0 rounded-full bg-blue-50 border border-blue-100 px-3 py-1 text-sm font-medium text-blue-600">
                    {uploader.progress}%
                </div>
            </div>
 
            <!-- Progress bar -->
            <div>
                <div class="relative h-3 overflow-hidden rounded-full bg-gray-200/80">
                    <div
                        class="relative h-full overflow-hidden rounded-full transition-all duration-500 ease-out"
                        style="width:{uploader.progress}%"
                    >
                        <div
                            class="absolute inset-0 bg-linear-to-r {isPaused
                                ? 'from-yellow-500 via-yellow-500 to-amber-600'
                                : 'from-indigo-500 via-indigo-500 to-purple-500'}"
                        ></div>
                        {#if !isPaused}
                            <div
                                class="absolute inset-0 animate-[shimmer_2s_linear_infinite]
                                bg-[linear-gradient(110deg,transparent,rgba(255,255,255,0.45),transparent)]
                                bg-size-[200%_100%]"
                            ></div>
                        {/if}
                    </div>
                </div>
 
                <!-- Meta -->
                <div class="mt-3 flex items-center justify-between text-sm">
                    <div class="flex items-center gap-4 text-gray-500">
                        <div>
                            <span class="text-gray-400">Speed</span>
                            <span class="ml-1 font-medium text-gray-700">
                                {isPaused ? "—" : formatSpeed(uploader.state.speedBytesPerSec)}
                            </span>
                        </div>
                        <div>
                            <span class="text-gray-400">ETA</span>
                            <span class="ml-1 font-medium text-gray-700">
                                {isPaused ? "—" : formatETA(uploader.state.etaSeconds)}
                            </span>
                        </div>
                    </div>
                    <p class="font-medium text-gray-700">{uploader.progress}% uploaded</p>
                </div>
            </div>
 
            <!-- Currently uploading (bounded by concurrency, safe to show live) -->
            {#if uploadingFiles.length > 0}
                <ul class="space-y-1 text-sm text-gray-600">
                    {#each uploadingFiles as file (file.id)}
                        <li class="flex items-center justify-between gap-2">
                            <span class="truncate">{file.relativePath}</span>
                            <span class="shrink-0 text-gray-400">
                                {Math.round((file.uploadedBytes / file.size) * 100)}%
                            </span>
                        </li>
                    {/each}
                </ul>
            {/if}
 
            {#if pendingCount > 0}
                <p class="text-sm text-gray-400">{pendingCount} more queued…</p>
            {/if}
 
            <!-- Failed files -- shown in full since there should only ever be a handful -->
            {#if failedFiles.length > 0}
                <div class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                    <p class="font-medium">{failedFiles.length} file{failedFiles.length === 1 ? "" : "s"} failed</p>
                    <ul class="mt-1 space-y-0.5">
                        {#each failedFiles as file (file.id)}
                            <li class="truncate">{file.relativePath} — {file.error}</li>
                        {/each}
                    </ul>
                </div>
            {/if}
 
            {#if uploader.state.error}
                <div class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                    {uploader.state.error}
                </div>
            {/if}
 
            <!-- See everything, including every uploaded/pending file -- only mounted on demand -->
            <button
                class="text-sm text-gray-500 underline underline-offset-2"
                onclick={() => (showAllFiles = !showAllFiles)}
            >
                {showAllFiles ? "Hide" : "Show"} all {uploader.state.files.length} files
            </button>
 
            {#if showAllFiles}
                <ul class="max-h-64 space-y-1 overflow-y-auto text-sm text-gray-600">
                    {#each uploader.state.files as file (file.id)}
                        <li class="flex items-center justify-between gap-2">
                            <span class="truncate">{file.relativePath}</span>
                            <span class="shrink-0 text-gray-400">{file.status}</span>
                        </li>
                    {/each}
                </ul>
            {/if}
 
            <!-- Actions -->
            <div class="flex items-center gap-3 pt-2">
                {#if isPaused}
                    <button
                        class="inline-flex items-center gap-2 rounded-xl bg-gray-900 px-4 py-2 text-sm
                            font-medium text-white transition hover:bg-black active:scale-[0.98]"
                        onclick={handleResumeUpload}
                    >
                        Resume
                    </button>
                {:else}
                    <button
                        class="inline-flex items-center gap-2 rounded-xl bg-gray-900 px-4 py-2 text-sm
                            font-medium text-white transition hover:bg-black active:scale-[0.98]"
                        onclick={handlePauseUpload}
                    >
                        Pause
                    </button>
                {/if}
 
                <button
                    class="inline-flex items-center gap-2 rounded-xl border px-4 py-2 text-sm border-red-200
                        bg-red-50 font-medium text-red-600 transition hover:bg-red-100 active:scale-[0.98]"
                    onclick={cancelUpload}
                >
                    X Cancel
                </button>
            </div>
        </div>
    {/if}
 
    {#if uploader.state.status === "completed"}
        <div class="flex flex-col">
            <!-- UploadCompleteBar likely needs its own update to the new `uploader.state.files` -->
            <UploadCompleteBar uploader={uploader} />
        </div>
    {/if}
</div>

<style>
    @keyframes shimmer {
        0% {
            background-position: 200% 0;
        }

        100% {
            background-position: -200% 0;
        }
    }
</style>
