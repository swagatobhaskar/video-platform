
type Options = {
    accept?: string; // e.g., "Image/*" or "video/*"
    multiple?: boolean;
    onFilesSelected?: (files: File[]) => void;
    onDragStateChange?: (dragging: boolean) => void;
};

export function createFileInputController(options: Options = {}) {
    let dragCounter = 0;

    function validate(files: File[]) {
        if (!options.accept) return files;

        const accepted_prefix = options.accept.replace("/*", "");

        return files.filter(
            file => file.type.startsWith(accepted_prefix)
        )
    }

    function handleFiles(fileList: FileList | null) {
        if (!fileList) return;

        let files = Array.from(fileList);

        if (!options.multiple) {
            files = files.slice(0, 1);
        }

        files = validate(files);

        options.onFilesSelected?.(files);
    }

    function handleDragEnter(e: DragEvent) {
        e.preventDefault();
        dragCounter++;
        options.onDragStateChange?.(true);
        // console.log("handleDragEnter");
    }

    function handleDragOver(e: DragEvent) {
        e.preventDefault();
        // console.log("handleDragOver");
    }

    function handleDragLeave(e: DragEvent) {
        e.preventDefault();
        dragCounter--;
        // console.log("handleDragLeave");
        
        if (dragCounter === 0) {
            options.onDragStateChange?.(false);
        }
    }

    function handleDrop(e: DragEvent) {
        e.preventDefault();
        dragCounter = 0;
        options.onDragStateChange?.(false);
        handleFiles(e.dataTransfer?.files || null);
        // console.log("handleDrop");
    }

    function handleFileChange(e: Event) {
        const input = e.target as HTMLInputElement;
        handleFiles(input.files);
    }

    return {
        handleDragEnter,
        handleDragOver,
        handleDragLeave,
        handleDrop,
        handleFileChange,
    };
}