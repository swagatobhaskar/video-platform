
// Drag events and handlers
// export function handleDragEnter(e: DragEvent) {
//     e.preventDefault();
//     isDragging = true;
// }

// export function handleDragOver(e: DragEvent) {
//     e.preventDefault();
// }

// export function handleDragLeave() {
//     isDragging = false;
// }

// export function handleDrop(e: DragEvent) {
//     e.preventDefault();
//     isDragging = false;

//     const files = e.dataTransfer?.files;
//     if (files && files.length > 0) {
//         file = files[0];
//         console.log("Dropped file: ", file);
//     }
// }

export function createDragAndDropHandlers(
    onDragStateChange: (dragging: boolean) => void,
    onFileDrop: (file: File) => void
) {
    function handleDragEnter(e: DragEvent) {
        e.preventDefault();
        onDragStateChange(true);
    }

    function handleDragOver(e: DragEvent) {
        e.preventDefault();
    }

    function handleDragLeave() {
        onDragStateChange(false);
    }

    function handleDrop(e: DragEvent) {
        e.preventDefault();
        onDragStateChange(false);

        const files = e.dataTransfer?.files;
        if (files && files.length > 0) {
            onFileDrop(files[0]);
        }
    }

    return {
        handleDragEnter,
        handleDragOver,
        handleDragLeave,
        handleDrop
    };
}
