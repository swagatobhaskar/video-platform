<script lang="ts">
    import Modal from "./Modal.svelte";
    import type { PreparedFolder } from "$lib/helpers/transcodedFolderSelection";
    
    let {
        open,
        prepared,
        selectionError,
        initiatingUpload,
        onUploadClick,
        onCancelSelection,
        handleDrop,
        handlePick
    } = $props<{
        open: boolean;
        prepared: PreparedFolder | null;
        selectionError: string | null;
        initiatingUpload: boolean;
        onUploadClick: () => void;
        onCancelSelection: () => void;
        handleDrop: (e: DragEvent) => Promise<void>;
        handlePick: (e: Event) => void;
    }>(); 

    let videoFolderInputEl = $state<HTMLInputElement | null>(null);

    // Props can't be reassigned from the child, so drag highlighting is local state.
    let dragging = $state(false);

    function openVideoFolderDialog() {
        videoFolderInputEl?.click();
    }

    const totalSize = $derived(
        prepared ? prepared.uploadEntries.reduce((total: number, e: {file: File}) => total + e.file.size, 0) : 0,
    );

    const segmentCount = $derived(
        prepared ? prepared.uploadEntries.filter((e: { file: File }) => e.file.name.endsWith(".m4s")).length : 0,
    );

    function formatDuration(seconds: number): string {
        const total = Math.round(seconds);
        const h = Math.floor(total / 3600);
        const m = Math.floor((total % 3600) / 60);
        const s = total % 60;
        return h > 0
            ? `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`
            : `${m}:${String(s).padStart(2, "0")}`;
    }
</script>

<!-- <Modal bind:open> -->
<Modal {open}>
    <section class="h-full flex flex-col items-center text-center relative">
        
        <!-- Inner border -->
        <div
            class="absolute inset-0 rounded-3xl p-3 border-2 border-dashed border-gray-400 flex items-center justify-center text-center"
            class:border-blue-500={dragging}
            class:bg-blue-50={dragging}
            role="button"
            tabindex="0"
            ondragover={(e) => { e.preventDefault(); dragging = true; }}
            ondragleave={(e) => {
                // dragleave also fires when moving over child elements; ignore those.
                if (!e.currentTarget.contains(e.relatedTarget as Node | null)) dragging = false;
            }}
            ondrop={(e) => { dragging = false; handleDrop(e); }}
            onclick={() => { if (!prepared) openVideoFolderDialog(); }}
            onkeydown={(e) => {
                if (!prepared && (e.key === "Enter" || e.key === " ")) {
                    e.preventDefault();
                    openVideoFolderDialog();
                }
            }}
        >
            {#if !prepared}
                <div class="flex flex-col items-center gap-3">
                    <!-- keep your existing <svg> icon here -->
 
                    <p>
                        Drop the parent folder here (the one containing dash/ and probe_result.json)
                        <br />
                        or
                    </p>
 
                    <button
                        type="button"
                        onclick={(e) => {
                            e.stopPropagation();
                            openVideoFolderDialog();
                        }}
                        class="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
                    >
                        Browse from device
                    </button>
                </div>
            {:else}
                <!-- Folder stats -->
                <div class="w-full h-full flex flex-col">
                    <div class="flex-1 min-h-0 flex items-center justify-center">
                        <div class="text-left">
                            <h2 class="text-xl font-semibold">Transcoded video ready</h2>
                            <p class="text-gray-500">{prepared.folderName}</p>
 
                            <div class="mt-4 space-y-2">
                                <p>Files: {prepared.uploadEntries.length}</p>
                                <p>Segments: {segmentCount}</p>
                                <p>Size: {(totalSize / 1024 / 1024).toFixed(2)} MB</p>
                                <p>
                                    {prepared.probe.width}X{prepared.probe.height} · {prepared.probe.codec} ·
                                    {prepared.probe.fps} fps · {formatDuration(prepared.probe.duration_seconds)}
                                </p>
                                {#if prepared.ignored.length > 0}
                                    <p class="text-sm text-gray-500">
                                        {prepared.ignored.length} other file{prepared.ignored.length === 1 ? "" : "s"} will be skipped
                                    </p>
                                {/if}
                            </div>
                        </div>
                    </div>
 
                    <!-- Actions -->
                    <div class="pt-5 flex justify-end gap-3">
                        <button
                            class="bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 px-5 rounded-xl transition cursor-pointer"
                            onclick={onCancelSelection}
                        >
                            Cancel
                        </button>
 
                        <button
                            class="bg-blue-600 hover:bg-blue-700 text-white py-2 px-5 rounded-xl transform shadow cursor-pointer"
                            onclick={onUploadClick}
                            disabled={initiatingUpload}
                        >
                            {initiatingUpload ? 'Uploading...' : 'Upload'}
                        </button>
                    </div>
                </div>
            {/if}
            <!-- Always mounted so the ref is stable. No `multiple` needed with webkitdirectory. -->
            <input
                type="file"
                class="hidden"
                webkitdirectory
                bind:this={videoFolderInputEl}
                onchange={handlePick}
            />
        </div>
        {#if selectionError}
            <p class="absolute bottom-2 text-sm text-red-600">{selectionError}</p>
        {/if}
    </section>
</Modal>
