
type UploadFileType = "video" | "image";

type FileInputPreference = {
    uploadFileType: UploadFileType;
}

type VideoMetadata = {
    duration: number;
    width: number;
    height: number;
    size: number;
    mimeType: string;
}

type ThumbnailMetadata = {
    width: number;
    height: number;
    size: number;
    format: string;
}

export function fileInputController({uploadFileType}: FileInputPreference) {
    const state = $state({
        isDragging: false,
        dragCounter: 0,
        error: null as string | null,
        selectedFile: null as File | null,
        videoMetadata: null as VideoMetadata | null,
        thumbnailMetadata: null as ThumbnailMetadata | null,
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

    const validateVideoFile = (file: File) : string | null => {
        const allowedVideoTypes = [
            "video/mp4",
            // "video/webm",
            // "video/quicktime", // .mov
        ];

        const maxFileSizeBytes = 10 * 1024 * 1024 * 1024; // 10 GB

        if (!allowedVideoTypes.includes(file.type)) {
            return "Unsupported video format. Please upload an MP4, WebM, or MOV video.";
        }

        if (file.size > maxFileSizeBytes) {
            return "Video must not exceed 10 GB.";
        }

        return null;
    }

    const validateImageFile = (file: File) : string | null => {
        const allowedImageTypes = [
            "image/png",
            "image/jpeg",
            "image/webp",
            "image/gif",
        ];
        const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB

        if (!allowedImageTypes.includes(file.type)) {
            return "Unsupported image format. Please upload a PNG, JPEG, WebP, or GIF image.";
        }

        if (file.size > MAX_FILE_SIZE_BYTES) {
            return "Image must not exceed 5 MB.";
        }

        return null;
    }

    const validateFile = (file: File) => {
        if (uploadFileType === "video") {
            return validateVideoFile(file);
        } else if (uploadFileType === "image") {
            // The function only returns error, otherwise null
            return validateImageFile(file);
        }
    }

    const getVideoMetadata = async (file: File): Promise<VideoMetadata> => {
        return new Promise((resolve, reject) => {
            const video = document.createElement("video");
            const objectURL = URL.createObjectURL(file);

            video.preload = "metadata";
            video.src = objectURL;

            video.onloadedmetadata = () => {
                URL.revokeObjectURL(objectURL);

                resolve({
                    duration: video.duration,
                    width: video.videoHeight,
                    height: video.videoHeight,
                    size: file.size,
                    mimeType: file.type,
                });
            };
            video.onerror = () => {
                URL.revokeObjectURL(objectURL);
                reject(new Error("Failed to load video metadata"));
            };
        });
    }

    const getThumbnailMetadata = async (file: File): Promise<ThumbnailMetadata> => {
        return new Promise((resolve, reject) => {
            // const image = document.createElement("img");
            const objectURL = URL.createObjectURL(file);

            const img = new Image();

            img.onload = () => {
                URL.revokeObjectURL(objectURL);                                                                                                                                                                                                                                                                         
                resolve({
                    width: img.width,
                    height: img.height,
                    size: file.size,
                    format: file.type,
                });
                
            };
            img.onerror = () => {
                URL.revokeObjectURL(objectURL);
                reject(new Error("Failed to load image metadata"));
            };
            img.src = objectURL;
        });
    }

    const handleProcessFile = async (file?: File) => {
        if (!file) return;

        // validateFile(file);

        state.selectedFile = file;
        
        console.log(file);

        if (uploadFileType === "video") {
            try {
                state.videoMetadata = await getVideoMetadata(file);
                console.log(state.videoMetadata);
            } catch (err) {
                console.error(err);
                state.error = "Could not read video metadata";
            }
        }

        if (uploadFileType === "image") {
            try {
                state.thumbnailMetadata = await getThumbnailMetadata(file);
                console.log(state.thumbnailMetadata);
            } catch (err) {
                console.error(err);
                state.error = "Could not read thumbnail metadata";
            }
        }
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

    function cancelSelectedFile() {
        state.selectedFile = null;
    }

    return {
        state,
        handleDragEnter,
        handleDragLeave,
        handleDragOver,
        handleDrop,
        handleFileSelect,
        cancelSelectedFile,
        validateFile,
    }
}
