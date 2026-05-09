
// type FileInputOptions = {
//     accept?: string[];
//     multiple?: boolean;
//     maxSizeBytes?: number;
// };

type FileValidationResult =
    | {
        valid: true;
        files: File[];
    }
    | {
        valid: false;
        error: string;
    };

export function createFileInputController(
    options: FileInputOptions = {}
) {
    const {
        accept = [],
        multiple = false,
        maxSizeBytes
    } = options;

    const state = $state({
        isDragging: false,
        dragCounter: 0,
        error: null as string | null
    });

    // ---------------------------------------------------
    // Validation
    // ---------------------------------------------------

    function validateFiles(files: File[]): FileValidationResult {
        if (files.length === 0) {
            return {
                valid: false,
                error: "No file selected"
            };
        }

        if (!multiple && files.length > 1) {
            return {
                valid: false,
                error: "Only one file allowed"
            };
        }

        for (const file of files) {
            // MIME validation
            if (accept.length > 0 && !accept.includes(file.type)) {
                return {
                    valid: false,
                    error: `Unsupported file type: ${file.type}`
                };
            }

            // SIZE validation
            if (maxSizeBytes && file.size > maxSizeBytes) {
                return {
                    valid: false,
                    error: `File too large: ${file.name}`
                }
            }
        }

        return { valid: true, files };
    }

    // ---------------------------------------------------
    // Shared File Extraction
    // ---------------------------------------------------

    function handleFiles(
        files: File[],
        // onFiles: (files: File[]) => void
    ) {
        const result = validateFiles(files);

        if (!result.valid) {
            state.error = result.error;
            return;
        }

        state.error = null;
        // onFiles(result.files);
    }

    // ---------------------------------------------------
    // Drag & Drop
    // ---------------------------------------------------

    // function onDragEnter(e: DragEvent) {
    //     e.preventDefault();
    //     state.dragCounter++;
    //     state.isDragging = true;
    //     // console.log("onDragEnter");
    // }

    // function onDragLeave(e: DragEvent) {
    //     e.preventDefault();
    //     state.dragCounter--;
    //     // console.log("onDragLeave");
    //     if (state.dragCounter <= 0) {
    //         state.isDragging = false;
    //         state.dragCounter = 0;
    //     }
    // }

    // function onDragOver(e: DragEvent) {
    //     e.preventDefault();
    //     // console.log("onDragOver");
    // }

    // function onDrop(
    //     e: DragEvent,
    //     // onFiles: (files: File[]) => void
    // ) {
    //     e.preventDefault();
    //     state.isDragging = false;
    //     state.dragCounter = 0;
        
    //     const files = Array.from(
    //         e.dataTransfer?.files ?? []
    //     )

    //     handleFiles(files);
    //     // handleFiles(files, onFiles);
    //     // console.log("onDrop");
    // }

    // // ---------------------------------------------------
    // // File Picker
    // // ---------------------------------------------------

    // function onFileSelect(
    //     e: Event,
    //     // onFiles: (files: File[]) => void
    // ) {
    //     const input = e.currentTarget as HTMLInputElement; // e.target ??

    //     const files = Array.from(input.files ?? []);

    //     // handleFiles(files, onFiles);
    //     handleFiles(files);

    //     // Allow re-selecting same file
    //     input.value = "";
    // }

    // // ---------------------------------------------------
    // // Helpers
    // // ---------------------------------------------------

    // const acceptAttribute = accept.join(",");

    // return {
    //     state,
    //     acceptAttribute,
    //     multiple,
    //     onDragEnter,
    //     onDragLeave,
    //     onDragOver,
    //     onDrop,
    //     onFileSelect,
    // };
}