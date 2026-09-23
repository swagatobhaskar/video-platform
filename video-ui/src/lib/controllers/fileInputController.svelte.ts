import { SvelteSet } from 'svelte/reactivity';

type UploadFileType = "video" | "image" | "transcoded-directory";

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
        selectedDirFiles: [] as File[],

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

        if (uploadFileType === "transcoded-directory") {
            handleProcessTranscodedFolder(files);
            return;
        }

        handleProcessFile(files[0]);
    }

    const validateTranscodedFolder = (files: File[]) : string | null => {
        if (files.length === 0) {
            return "The transcoded video folder is empty.";
        }

        const paths = files.map(file => file.webkitRelativePath);

        // Every file should have a relative path.
        if (paths.some(path => !path)) {
            return "Could not determine the folder structure.";
        }

        // Get the selected root directory
        const rootFolders = new SvelteSet(
            paths.map(path => path.split("/")[0])
        );

        if (rootFolders.size !== 1) {
            return "Please select exactly one transcoded video folder.";
        }

        const root = [...rootFolders][0];

        const requiredFiles = [
            `${root}/dash/manifest.mpd`,
            `${root}/dash/master.m3u8`,
        ];

        for (const requiredFile of requiredFiles) {
            if (!paths.includes(requiredFile)) {
                return `Missing required file: ${requiredFile.replace(`${root}/`, "")}`;
            }
        }

        // Everything must be inside dash/
        const invalidFiles = paths.filter(path => {
            const relativePath = path.slice(root.length + 1);
            return !relativePath.startsWith("dash/");
        });

        if (invalidFiles.length > 0) {
            return "The transcoded folder may only contain a dash folder.";
        }

        const dashFiles = files.filter(file => file.webkitRelativePath.startsWith(`${root}/dash/`))

        for (const file of dashFiles) {
            const filename = file.name;

            const allowed = 
                filename === "manifest.mpd" ||
                filename === "master.m3u8" ||
                filename.endsWith(".m3u8") ||
                filename.endsWith(".mpd") ||
                filename.endsWith(".m4s") ||
                filename.endsWith(".mp4");

            if (!allowed) {
                return `Unsupported file in dash folder: ${filename}`;
            }
        }

        // At least one media segment should exist
        const hasSegment = dashFiles.some(file => file.name.endsWith(".m4s"));

        if (!hasSegment) {
            return "The dash folder does not contain any .m4s media segments.";
        }

        return null;
    };

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
                    width: video.videoWidth,
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

    const handleProcessTranscodedFolder = (files: File[]) => {
        state.error = null;

        const error = validateTranscodedFolder(files);

        if (error) {
            state.selectedDirFiles = [];
            state.error = error;
            return;
        }

        state.selectedDirFiles = files;

        console.log("Transcoded files:", files);
    };

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

    const handleFolderSelect = (e: Event) => {
        const input = e.currentTarget as HTMLInputElement;
        const files = Array.from(input.files ?? []);
        input.value = "";
        handleProcessTranscodedFolder(files);
    };

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
        state.selectedDirFiles = [];
        state.error = null;
    }

    return {
        state,
        handleDragEnter,
        handleDragLeave,
        handleDragOver,
        handleDrop,
        handleFileSelect,
        handleFolderSelect,
        cancelSelectedFile,
        validateFile,
        validateTranscodedFolder,
    }
}
