import { SvelteMap } from "svelte/reactivity";

type UploadFileStatus =
    | "pending"
    | "presigning"
    | "uploading"
    | "uploaded"
    | "failed"
    | "cancelled";

type UploadFile = {
    id: string;
    file: File;
    relativePath: string;
    objectKey: string | null;
    uploadUrl: string | null;
    size: number;
    uploadedBytes: number;
    status: UploadFileStatus;
    attempts: number;
    error: string | null;
};

type PresignRequestFile = {
    file_id: string;
    relative_path: string;
    size: number;
    content_type: string;
};

type PresignResponseFile = {
    file_id: string;
    object_key: string;
    upload_url: string;
};

type UploadOptions = {
    videoId: string;
    uploadSessionId: string;
    batchSize?: number;
    concurrency?: number;
    maxRetries?: number;
};

const DEFAULT_BATCH_SIZE = 50;
const DEFAULT_CONCURRENCY = 6;
const DEFAULT_MAX_RETRIES = 4;

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

function getContentType(file: File): string {
    if (file.type) {
        return file.type;
    }

    switch (file.name.split(".").pop()?.toLowerCase()) {
        case "m4s":
            return "video/iso.segment";
        case "mp4":
            return "video/mp4";
        case "m3u8":
            return "application/vnd.apple.mpegurl";
        case "mpd":
            return "application/dash+xml";
        default:
            return "application/octet-stream";
    }
}

function getBackoffDelay(attempt: number): number {
    const base = 1000;
    const max = 15_000;
    const exponential = base * 2 ** attempt;

    // Small jitter prevents many requests retrying simultaneously.
    const jitter = Math.random() * 500;

    return Math.min(exponential + jitter, max);
}

export function createTranscodedFolderUploader() {
    const state = $state({
        status: "idle" as
            | "idle"
            | "uploading"
            | "paused"
            | "completed"
            | "failed",

        files: [] as UploadFile[],
        videoId: null as string | null,
        uploadSessionId: null as string | null,
        totalBytes: 0,
        uploadedBytes: 0,
        error: null as string | null,
    });

    let abortController: AbortController | null = null;

    let batchSize = DEFAULT_BATCH_SIZE;
    let concurrency = DEFAULT_CONCURRENCY;
    let maxRetries = DEFAULT_MAX_RETRIES;

    let stopping = false;

    function initializeFiles(files: File[]) {
        state.files = files.map(file => ({
            id: crypto.randomUUID(),
            file,
            relativePath: file.webkitRelativePath || file.name,
            objectKey: null,
            uploadUrl: null,
            size: file.size,
            uploadedBytes: 0,
            status: "pending",
            attempts: 0,
            error: null,
        }));

        state.totalBytes = files.reduce((total, file) => total + file.size, 0);
        state.uploadedBytes = 0;
        state.error = null;
        state.status = "idle";
    }

    async function requestUploadUrls(
        videoId: string,
        uploadSessionId: string,
        files: UploadFile[],
    ): Promise<void> {
        if (files.length === 0) {
            return;
        }

        for (const file of files) {
            file.status = "presigning";
        }

        const requestFiles: PresignRequestFile[] = 
            files.map(file => ({
                file_id: file.id,
                relative_path: file.relativePath,
                size: file.size,
                content_type: getContentType(file.file),
            }));

        const response = await fetch(
            `/api/videos/${videoId}/transcoded/upload-urls`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    upload_session_id: uploadSessionId,
                    files: requestFiles,
                }),
            }
        );

        if (!response.ok) {
            throw new Error(`Failed to obtain upload URLs (${response.status})`);
        }

        const data: {files: PresignResponseFile[];} = await response.json();

        const byId = new SvelteMap(
            data.files.map(file => [
                file.file_id,
                file,
            ])
        );

        for (const file of files) {
            const presigned = byId.get(file.id);

            if (!presigned) {
                throw new Error(`Backend did not return an upload URL for ${file.relativePath}`);
            }

            file.objectKey = presigned.object_key;
            file.uploadUrl = presigned.upload_url;
        }
    }

    async function uploadSingleFile(uploadFile: UploadFile): Promise<void> {
        if (!uploadFile.uploadUrl) {
            throw new Error(`No upload URL for ${uploadFile.relativePath}`);
        }

        while (uploadFile.attempts <= maxRetries) {
            if (stopping) {
                return;
            }

            uploadFile.status = "uploading";
            uploadFile.error = null;

            try {
                const response = await fetch(
                    uploadFile.uploadUrl,
                    {
                        method: "PUT",
                        headers: {
                            "Content-Type": getContentType(uploadFile.file),
                        },
                        body: uploadFile.file,
                        signal: abortController?.signal,
                    }
                );

                if (!response.ok) {
                    throw new Error(`R2 upload failed with HTTP ${response.status}`);
                }

                uploadFile.uploadedBytes = uploadFile.size;
                uploadFile.status = "uploaded";
                return;
            } catch (error) {
                // Pause/cancel isn't a real upload failure.
                if (error instanceof DOMException && error.name === "AbortError") {
                    return;
                }

                uploadFile.attempts++;

                if (uploadFile.attempts > maxRetries) {
                    uploadFile.status = "failed";
                    uploadFile.error = error instanceof Error ? error.message : "Upload Failed";
                    throw error;
                }

                uploadFile.error = error instanceof Error ? error.message : "Upload failed";

                await sleep(getBackoffDelay(uploadFile.attempts - 1));
            }
        }
    }

    async function recordUploadFile(
        videoId: string,
        uploadSessionId: string,
        uploadFile: UploadFile,
    ) {
        const response = await fetch(
            `/api/video/${videoId}/transcoded/record-uploaded-file`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },

                body: JSON.stringify({
                    upload_session_id: uploadSessionId,
                    file_id: uploadFile.id,
                    relative_path: uploadFile.relativePath,
                    object_key: uploadFile.objectKey,
                    size: uploadFile.size,
                }),

                signal: abortController?.signal,
            }
        );

        if (!response.ok) {
            throw new Error(`Failed to record uploaded file (${response.status})`);
        }
    }

    async function uploadWithWorkerPool(
        videoId: string,
        uploadSessionId: string,
        files: UploadFile[],
    ) {
        let nextIndex = 0;

        async function worker() {
            while (true) {
                if (stopping) {
                    return;
                }

                const index = nextIndex++;

                if (index >= files.length) {
                    return;
                }

                const uploadFile = files[index];

                if (uploadFile.status === "uploaded") {
                    continue;
                }

                try {
                    await uploadSingleFile(uploadFile);

                    if (uploadFile.status !== "uploaded") {
                        continue;
                    }

                    await recordUploadFile(
                        videoId,
                        uploadSessionId,
                        uploadFile
                    );

                    state.uploadedBytes += uploadFile.size;
                } catch (error) {
                    if (stopping) {
                        return;
                    }

                    console.error("File upload failed:", uploadFile.relativePath, error);
                }
            }
        }

        const workers = Array.from(
            {length: Math.min(concurrency, files.length),},
            () => worker()
        );

        await Promise.all(workers);
    }

    async function upload(files: File[], options: UploadOptions) {
        if (state.status === "uploading") {
            throw new Error("An upload is already running.");
        }

        initializeFiles(files);

        state.videoId = options.videoId;
        state.uploadSessionId = options.uploadSessionId;

        batchSize = options.batchSize ?? DEFAULT_BATCH_SIZE;
        concurrency = options.concurrency ?? DEFAULT_CONCURRENCY;
        maxRetries = options.maxRetries ?? DEFAULT_MAX_RETRIES;
        stopping = false;
        abortController = new AbortController();

        state.status = "uploading";

        try {
            for (let start  = 0; start < state.files.length; start += batchSize) {
                if (stopping) {
                    return;
                }
                const batch = state.files.slice(start, start + batchSize);
                const pendingBatch = batch.filter(file => file.status !== "uploaded");

                if (pendingBatch.length === 0) {
                    continue;
                }

                await requestUploadUrls(
                    options.videoId,
                    options.uploadSessionId,
                    pendingBatch
                );

                await uploadWithWorkerPool(
                    options.videoId,
                    options.uploadSessionId,
                    pendingBatch
                );

                const failed = pendingBatch.some(file => file.status === "failed");

                if (failed) {
                    state.status = "failed";
                    state.error = "One or more files failed to upload.";
                    return;
                }
            }

            if (!stopping) {
                await complete(options.videoId, options.uploadSessionId);
                state.status = "completed";
            }
        } catch (error) {
            if (stopping) {
                return;
            }

            state.status = "failed";
            state.error = error instanceof Error ? error.message : "Upload failed";
        }
    }

    async function complete(videoId: string, uploadSessionId: string) {
        const files = state.files
            .filter(file => file.status === "uploaded")
            .map(file => ({file_id: file.id, relative_path: file.relativePath, object_key: file.objectKey, size: file.size,}));

        const response = await fetch(
            `/api/video/${videoId}/transcoded/complete`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },

                body: JSON.stringify({
                    upload_session_id: uploadSessionId,
                    files,
                }),
            }
        );

        if (!response.ok) {
            throw new Error(`Failed to complete upload (${response.status})`);
        }
    }

    function pause() {
        if (state.status !== "uploading") {
            return;
        }
        stopping = true;
        abortController?.abort();
        state.status = "paused";
    }

    function resume() {
        if(state.status !== "paused") {
            return;
        }
        if (!state.videoId || !state.uploadSessionId) {
            throw new Error("Upload session information is missing.");
        }
        stopping = false;

        upload(
            state.files.map(file => file.file),
            {
                videoId: state.videoId,
                uploadSessionId: state.uploadSessionId,
                batchSize,
                concurrency,
                maxRetries,
            }
        );
    }

    function cancel() {
        stopping = true;
        abortController?.abort();
        for (const file of state.files) {
            if (file.status !== "uploaded") {
                file.status = "cancelled";
            }
        }
    }

    const progress = $derived.by(() => {
        if (state.totalBytes === 0) {
            return 0;
        }

        return Math.round((state.uploadedBytes / state.totalBytes) * 100);
    });

    const uploadedFileCount = $derived(
        state.files.filter(file => file.status === "uploaded").length
    );

    const failedFileCount = $derived(
        state.files.filter(file => file.status === "failed").length
    );

    return {
        state,
        progress,
        uploadedFileCount,
        failedFileCount,
        initializeFiles,
        upload,
        pause,
        resume,
        cancel,
    };
}


export function uploadFileWithProgress(
    file: UploadFile,
    signal: AbortSignal,
): Promise<void> {
    return new Promise((resolve, reject) => {

        const xhr = new XMLHttpRequest();

        xhr.open("PUT", file.uploadUrl!);

        xhr.setRequestHeader("Content-Type", getContentType(file.file));

        xhr.upload.onprogress = (event) => {

            if (event.lengthComputable) {
                file.uploadedBytes = event.loaded;
            }
        };

        xhr.onload = () => {

            if (xhr.status >= 200 && xhr.status < 300) {
                file.uploadedBytes = file.size;
                resolve();
            } else {
                reject(new Error(`R2 returned HTTP ${xhr.status}`));
            }
        };

        xhr.onerror = () => {
            reject(new Error("Network error while uploading file."));
        };

        xhr.onabort = () => {
            reject(new DOMException("Upload aborted", "AbortError"));
        };

        signal.addEventListener("abort", () => xhr.abort(), { once: true });

        xhr.send(file.file);
    });
}