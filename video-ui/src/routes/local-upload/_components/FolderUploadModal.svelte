<script lang="ts">
    import Modal from "./Modal.svelte";

    import { fileInputController } from "$lib/controllers/fileInputController.svelte";
    type FileInputController = ReturnType<typeof fileInputController>;

    let { open, onUploadClick, folderInputController } = $props<{
        open: boolean;
        onUploadClick: () => void;
        folderInputController: FileInputController;
    }>();

    let videoFolderInputEl = $state<HTMLInputElement | null>(null);
    let initiatingUpload: boolean = $state(false);

    function openVideoFolderDialog() {
        videoFolderInputEl?.click();
    }
    
    const selectedFiles = $derived(
        folderInputController.state.selectedDirFiles
    );

    const hasSelectedFolder = $derived(
        selectedFiles.length > 0
    );

    const totalSize = $derived(
        selectedFiles.reduce((total: number, file: File) => total + file.size, 0)
    );

    const segmentCount = $derived(
        selectedFiles.filter((file: File) => file.name.endsWith(".m4s")).length
    );
</script>

<!-- <Modal bind:open> -->
<Modal {open}>
    <section class="h-full flex flex-col items-center text-center relative">
        
        <!-- Inner border -->
        <div
            class="absolute inset-0 rounded-3xl p-3 border-2 border-dashed border-gray-400 flex items-center justify-center text-center"
            role="button"
            tabindex="0"
            ondragenter={folderInputController.handleDragEnter}
            ondragleave={folderInputController.handleDragLeave}
            ondragover={folderInputController.handleDragOver}
            ondrop={folderInputController.handleDrop}
            onclick={openVideoFolderDialog}
            class:border-blue-500={folderInputController.state.isDragging}
            class:bg-blue-50={folderInputController.state.isDragging}

            onkeydown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    openVideoFolderDialog();
                }
            }}
        >
            <!-- Show input options if file isn't selcted -->
            <!-- {#if folderInputController.state.selectedDirFiles.length === 0} -->
            {#if !hasSelectedFolder}
                <div class="flex flex-col items-center gap-3">

                    <svg fill="#C4C4C4" viewBox="-2.1 -2.1 39.20 39.20" version="1.1" xmlns="http://www.w3.org/2000/svg" stroke="#C4C4C4" stroke-width="0.00035">
                        <g id="SVGRepo_bgCarrier" stroke-width="0"></g>
                        <g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round" stroke="#CCCCCC" stroke-width="0.7"></g>
                        <g id="SVGRepo_iconCarrier">
                            <title>upload1</title>
                            <path d="M29.426 15.535c0 0 0.649-8.743-7.361-9.74-6.865-0.701-8.955 5.679-8.955 5.679s-2.067-1.988-4.872-0.364c-2.511 1.55-2.067 4.388-2.067
                            4.388s-5.576 1.084-5.576 6.768c0.124 5.677 6.054 5.734 6.054 5.734h9.351v-6h-3l5-5 5 5h-3v6h8.467c0 0 5.52 0.006 6.295-5.395 0.369-5.906-5.336-7.070-5.336-7.070z"></path>
                        </g>
                    </svg>

                    <p>
                        Drop folder containing transcoded video files here
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

                    <input
                        type="file"
                        class="hidden"
                        multiple
                        webkitdirectory                        
                        bind:this={videoFolderInputEl}
                        onchange={folderInputController.handleFolderSelect}
                    />
                </div>
            {:else}
                <!-- Show Folder stats  -->
                <div class="w-full h-full flex flex-col">
                    <div class="flex-1 min-h-0 flex items-center justify-center">
                        <div class="text-left">
                            <h2 class="text-xl font-semibold">
                                Transcoded video ready
                            </h2>
                            <div class="mt-4 space-y-2">
                                <p>Files: {selectedFiles.length}</p>
                                <p>Segments: {segmentCount}</p>
                                <p>Size: {(totalSize / 1024 / 1024).toFixed(2)} MB</p>
                            </div>
                        </div>
                    </div>

                    <!-- Actions - Upload & Cancel Buttons -->
                    <div class="pt-5 flex justify-end gap-3">
                        <button
                            class="bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 px-5 rounded-xl transition cursor-pointer"
                            onclick={() => {
                                folderInputController.cancelSelectedFile();
                            }}
                        >
                            Cancel
                        </button>

                        <button
                            class="bg-blue-600 hover:bg-blue-700 text-white py-2 px-5 rounded-xl transform shadow cursor-pointer"
                            onclick={onUploadClick}
                            disabled={initiatingUpload}
                        >
                            { initiatingUpload ? 'Uploading...' : 'Upload' }
                        </button>
                    </div>
                </div>
            {/if}
        </div>
        {#if folderInputController.state.error}
            <p class="error">{folderInputController.state.error}</p>
        {/if}
    </section>
</Modal>
