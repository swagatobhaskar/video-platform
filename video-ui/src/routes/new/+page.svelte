<script lang="ts">
    // Video file selection handler
    let videoFileInputEl = $state<HTMLInputElement | null>(null);

    function openVideoFileDialog() {
        videoFileInputEl?.click();
    }

    type UploadFileType = "video" | "image";

    type FileInputPreference = {
        uploadFileType: UploadFileType;
    }
    
    function fileInputController({uploadFileType}: FileInputPreference) {
        const state = $state({
            isDragging: false,
            dragCounter: 0,
            error: null,
        });

        const handleDragEnter = (e: DragEvent) => {
            e.preventDefault();
            state.dragCounter ++;
            state.isDragging = true;
            console.log("on drag enter");
        }

        const handleDragLeave = (e: DragEvent) => {
            e.preventDefault();
            // state.isDragging = false;
            state.dragCounter --;
    
            if (state.dragCounter <= 0) {
                state.dragCounter = 0;
                state.isDragging = false;
            }
            
            console.log("on drag leave");
        }

        const handleDragOver = (e: DragEvent) => {
            e.preventDefault();
            console.log("on drag over");
        }

        const handleDrop = (e: DragEvent) => {
            e.preventDefault();
            state.isDragging = false;
            state.dragCounter = 0;
            const files = Array.from(e.dataTransfer?.files ?? [])
            handleProcessFile(files[0]);
        }

        const validateVideoFile = (file: File) => {}
        const validateImageFile = (file: File) => {}

        const validateFile = (file: File) => {
            if (uploadFileType === "video") {
                const validatedVideoFile = validateVideoFile(file);
                // return file or error
            } else if (uploadFileType === "image") {
                const validatedImageFile = validateImageFile(file);
                // return file or error
            }
        }

        const handleProcessFile = (file: File) => {
            validateFile(file);
            console.log(file);
        }

        const handleFileSelect = (e: Event) => {
            const input = e.currentTarget as HTMLInputElement;
            const files = Array.from(input.files ?? []);
            // handle the selected file
            const file = files[0];

            // Allow re-selecting same file
            input.value = "";

            // handle selected file
            handleProcessFile(file);
        }

        return {
            state,
            handleDragEnter,
            handleDragLeave,
            handleDragOver,
            handleDrop,
            handleFileSelect,
        }
    }

    const videoInput = fileInputController({uploadFileType: "video"});
 
</script>

<!-- Calculating the height of this page: subtract 100vh from the header height -->

<div class="h-[calc(100vh-4rem)] md:h-[calc(100vh-5rem)] flex items-center justify-center">
    <!-- Video Drop -->
    <div class="w-screen md:w-3/5 h-4/5 md:h-3/5 bg-white rounded-4xl shadow-2xl relative">
        <!-- Inner border -->
        <div
            class="absolute inset-5 border-2 border-dashed border-gray-400 rounded-3xl pointer-events-auto
                flex items-center justify-center text-center p-10"
            role="button"
            tabindex="0"
            ondragenter={videoInput.handleDragEnter}
            ondragleave={videoInput.handleDragLeave}
            ondragover={videoInput.handleDragOver}
            ondrop={videoInput.handleDrop}
            class:border-blue-500={videoInput.state.isDragging}
            class:bg-blue-50={videoInput.state.isDragging}
            onclick={openVideoFileDialog}
            
            onkeydown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    openVideoFileDialog();
                }
            }}
        >
            <div class="flex flex-col items-center gap-3">
                <p>
                    Drop video here
                    <br />
                    or
                </p>

                <button
                    type="button"
                    onclick={openVideoFileDialog}
                    class="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
                >
                    Browse from device
                </button>

                <input
                    type="file"
                    accept="video/*"
                    class="hidden"
                    bind:this={videoFileInputEl}
                    onchange={videoInput.handleFileSelect}
                />
            </div>
        </div>
        {#if videoInput.state.error}
            <p class="error">{videoInput.state.error}</p>
        {/if}
    </div>
</div>
