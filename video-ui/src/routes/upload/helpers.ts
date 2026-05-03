
export function splitFileIntoChunks(file: File, chunkSizeMB: number = 5): Blob[] {
    const chunkSize = chunkSizeMB * 1024 * 1024; // Convert MB to bytes
    const chunks: Blob[] = [];
    let offset = 0;

    while (offset < file.size) {
        const chunk = file.slice(offset, offset + chunkSize);
        chunks.push(chunk);
        offset += chunkSize;
    }

    return chunks;
}

export function formatSpeed(bytesPerSec: number): string {
    if (bytesPerSec < 1024) return `${bytesPerSec.toFixed(0)} B/s`;
    if (bytesPerSec < 1024 * 1024) {
        return `${(bytesPerSec / 1024).toFixed(1)} KB/s`;
    }

    return `${(bytesPerSec / (1024 * 1024)).toFixed(1)} MB/s`;
}

export function formatETA(seconds: number): string {
    if (!isFinite(seconds)) return "Calculating...";
    if (seconds < 60) return `${Math.ceil(seconds)}s`;

    const min = Math.floor(seconds / 60);
    const sec = Math.ceil(seconds % 60);
    return `${min}m ${sec}s`;
}


// ---------------- XHR Upload ----------------

export function uploadChunkWithProgress(
    url: string,
    chunk: Blob,
    onProgress: ( loaded: number, total: number ) => void,
    signal: AbortSignal
): Promise<{ etag: string | null }> {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        // If the signal is already aborted before calling this function
        if (signal.aborted) {
            xhr.abort();
            return reject(new Error("Upload Cancelled"));
        }

        // Prevent memory leak
        const abortHandler = () => {
            xhr.abort();
        };

        signal.addEventListener("abort", abortHandler);

        xhr.open("PUT", url, true);

        xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
                onProgress(event.loaded, event.total);
            }
        };

        const cleanup = () => {
            signal.removeEventListener("abort", abortHandler);
        };

        xhr.onload = () => {
            cleanup();
            if (xhr.status >= 200 && xhr.status < 300) {
                const etag = xhr.getResponseHeader("ETag");
                resolve({ etag });
            } else {
                reject(new Error(`XHR upload failed: ${xhr.status}`));
            }
        };

        xhr.onerror = () => {
            cleanup();
            reject(new Error("XHR network error"));
        }

        xhr.onabort = () => {
            cleanup();
            reject(new Error("Upload Cancelled"));
        }

        xhr.send(chunk);
    });
}
