import { SvelteMap } from "svelte/reactivity";

type UploadFileStatus =
    | "pending"
    | "presigning"
    | "uploading"
    | "uploaded"
    | "failed"
    | "cancelled";

export type UploadFile = {
    id: string;
    file: File;
    relativePath: string;
    objectKey: string | null;
    uploadUrl: string | null;
    size_bytes: number;
    uploadedBytes: number;
    status: UploadFileStatus;
    attempts: number;
    error: string | null;
};

type PresignRequestFile = {
    file_id: string;
    relative_path: string;
    size_bytes: number;
    content_type: string;
};

type PresignResponseFile = {
    file_id: string;
    object_key: string;
    // Omitted by the backend when already_uploaded is true.
    upload_url?: string;
    already_uploaded: boolean;
};

type UploadOptions = {
    videoId: string;
    transcodedUploadSessionId: string;
    batchSize?: number;
    concurrency?: number;
    maxRetries?: number;
};

const DEFAULT_BATCH_SIZE = 50;
const DEFAULT_CONCURRENCY = 6;
const DEFAULT_MAX_RETRIES = 4;

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const EXTENSION_CONTENT_TYPES: Record<string, string> = {
    m4s: "video/iso.segment",
    mp4: "video/mp4",
    m3u8: "application/vnd.apple.mpegurl",
    mpd: "application/dash+xml",
};

function getContentType(file: File): string {
    if (file.type) return file.type;
    const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
    return EXTENSION_CONTENT_TYPES[ext] ?? "application/octet-stream";
}

function getBackoffDelay(attempt: number): number {
    const base = 1000;
    const max = 15_000;
    const exponential = base * 2 ** attempt;
    const jitter = Math.random() * 500; // spreads out simultaneous retries
    return Math.min(exponential + jitter, max);
}

function apiUrl(videoId: string, path: string): string {
    return `/api/video/transcoded-upload/${videoId}/${path}`;
}

async function postJson<T>(url: string, body: unknown, signal?: AbortSignal): Promise<T> {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal,
    });

    if (!response.ok) {
        throw new Error(`Request to ${url} failed (${response.status})`);
    }

    return response.status === 204 ? (undefined as T) : response.json();
}

/** For the pause/resume/abort endpoints, which take transcoded_upload_session_id as a query param, not a JSON body. */
async function postWithQuery<T>(url: string, query: Record<string, string>): Promise<T> {
    const response = await fetch(`${url}?${new URLSearchParams(query)}`, { method: "POST" });

    if (!response.ok) {
        throw new Error(`Request to ${url} failed (${response.status})`);
    }

    return response.status === 204 ? (undefined as T) : response.json();
}

/** PUTs one file to its presigned R2 URL, reporting live progress via `file.uploadedBytes`. */
function putFileToR2(file: UploadFile, signal: AbortSignal): Promise<void> {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open("PUT", file.uploadUrl!);
        xhr.setRequestHeader("Content-Type", getContentType(file.file));

        xhr.upload.onprogress = event => {
            if (event.lengthComputable) file.uploadedBytes = event.loaded;
        };

        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                file.uploadedBytes = file.size_bytes;
                resolve();
            } else {
                reject(new Error(`R2 upload failed with HTTP ${xhr.status}`));
            }
        };

        xhr.onerror = () => reject(new Error("Network error while uploading file."));
        xhr.onabort = () => reject(new DOMException("Upload aborted", "AbortError"));

        signal.addEventListener("abort", () => xhr.abort(), { once: true });
        xhr.send(file.file);
    });
}

export function createTranscodedFolderUploader() {
    const state = $state({
        status: "idle" as
            | "idle"
            | "uploading"
            | "paused"
            | "completed"
            | "failed"
            | "cancelled",

        files: [] as UploadFile[],
        videoId: null as string | null,
        transcodedUploadSessionId: null as string | null,
        totalBytes: 0,
        error: null as string | null,

        // Bytes/sec over a trailing window, and estimated seconds remaining.
        // null speed/eta means "not enough data yet" (just started, or paused).
        speedBytesPerSec: 0,
        etaSeconds: null as number | null,
    });

    let abortController: AbortController | null = null;
    let batchSize = DEFAULT_BATCH_SIZE;
    let concurrency = DEFAULT_CONCURRENCY;
    let maxRetries = DEFAULT_MAX_RETRIES;
    let stopping = false;

    // Rolling window of {time, bytes} samples, used to smooth the speed reading
    // instead of just diffing two consecutive ticks (which is noisy per-second).
    const SPEED_WINDOW_MS = 5000;
    let speedSamples: { time: number; bytes: number }[] = [];
    let speedInterval: ReturnType<typeof setInterval> | null = null;

    function startSpeedTracking() {
        speedSamples = [{time:  Date.now(), bytes: uploadedBytes}];
        state.speedBytesPerSec = 0;
        state.etaSeconds = null;

        speedInterval = setInterval(() => {
            const now = Date.now();
            speedSamples.push({ time: now, bytes: uploadedBytes });
            while (speedSamples.length > 2 && now - speedSamples[0].time > SPEED_WINDOW_MS) {
                speedSamples.shift();
            }
 
            const oldest = speedSamples[0];
            const elapsedSec = (now - oldest.time) / 1000;
            const bytesDelta = uploadedBytes - oldest.bytes;
 
            state.speedBytesPerSec = elapsedSec > 0 ? bytesDelta / elapsedSec : 0;
 
            const remainingBytes = state.totalBytes - uploadedBytes;
            state.etaSeconds =
                state.speedBytesPerSec > 0 ? remainingBytes / state.speedBytesPerSec : null;
        }, 1000);
    }

    function stopSpeedTracking() {
        if (speedInterval) clearInterval(speedInterval);
        speedInterval = null;
        state.speedBytesPerSec = 0;
        state.etaSeconds = null;
    }

    function initializeFiles(files: File[]) {
        state.files = files.map(file => ({
            id: crypto.randomUUID(),
            file,
            relativePath: file.webkitRelativePath || file.name,
            objectKey: null,
            uploadUrl: null,
            size_bytes: file.size,
            uploadedBytes: 0,
            status: "pending",
            attempts: 0,
            error: null,
        }));

        state.totalBytes = files.reduce((total, file) => total + file.size, 0);
        state.error = null;
        state.status = "idle";
    }

    async function requestUploadUrls(
        videoId: string,
        transcodedUploadSessionId: string,
        files: UploadFile[],
    ): Promise<void> {
        if (files.length === 0) return;

        for (const file of files) file.status = "presigning";

        const requestFiles: PresignRequestFile[] = files.map(file => ({
            file_id: file.id,
            relative_path: file.relativePath,
            size_bytes: file.size_bytes,
            content_type: getContentType(file.file),
        }));

        const { files: presigned } = await postJson<{ files: PresignResponseFile[] }>(
            apiUrl(videoId, "presign-batch"),
            { transcoded_upload_session_id: transcodedUploadSessionId, files: requestFiles },
        );

        const byId = new SvelteMap(presigned.map(file => [file.file_id, file]));

        for (const file of files) {
            const match = byId.get(file.id);
            if (!match) {
                throw new Error(`Backend did not return an upload URL for ${file.relativePath}`);
            }

            file.objectKey = match.object_key;

            // The backend already has this file recorded as UPLOADED (e.g. after
            // a resume) -- nothing to PUT, no upload_url is even sent for it.
            if (match.already_uploaded) {
                file.status = "uploaded";
                file.uploadedBytes = file.size_bytes;
                continue;
            }

            if (!match.upload_url) {
                throw new Error(`Backend did not return an upload URL for ${file.relativePath}`);
            }

            file.uploadUrl = match.upload_url;
        }
    }

    async function uploadSingleFile(file: UploadFile): Promise<void> {
        if (!file.uploadUrl) throw new Error(`No upload URL for ${file.relativePath}`);

        while (file.attempts <= maxRetries) {
            if (stopping) return;

            file.status = "uploading";
            file.error = null;
            file.uploadedBytes = 0;

            try {
                await putFileToR2(file, abortController!.signal);
                file.status = "uploaded";
                return;
            } catch (error) {
                // Pause/cancel isn't a real upload failure.
                if (error instanceof DOMException && error.name === "AbortError") return;

                file.attempts++;
                file.error = error instanceof Error ? error.message : "Upload failed";

                if (file.attempts > maxRetries) {
                    file.status = "failed";
                    throw error;
                }

                await sleep(getBackoffDelay(file.attempts - 1));
            }
        }
    }

    async function recordUploadFile(
        videoId: string,
        transcodedUploadSessionId: string,
        file: UploadFile,
    ): Promise<void> {
        await postJson(
            apiUrl(videoId, "record-uploaded-file"),
            {
                transcoded_upload_session_id: transcodedUploadSessionId,
                file_id: file.id,
                relative_path: file.relativePath,
                object_key: file.objectKey,
                size: file.size_bytes,
            },
            abortController?.signal,
        );
    }

    async function uploadWithWorkerPool(
        videoId: string,
        transcodedUploadSessionId: string,
        files: UploadFile[],
    ): Promise<void> {
        let nextIndex = 0;

        async function worker() {
            while (true) {
                if (stopping) return;

                const index = nextIndex++;
                if (index >= files.length) return;

                const file = files[index];
                if (file.status === "uploaded") continue;

                try {
                    await uploadSingleFile(file);
                    // May be this check is not required since uploadSingleFile() already has a clear contract:
                    // it returns normally when the upload succeeds, and throws when it ultimately fails.
                    // if (file.status !== "uploaded") continue;

                    await recordUploadFile(videoId, transcodedUploadSessionId, file);
                } catch (error) {
                    if (stopping) return;
                    console.error("File upload failed:", file.relativePath, error);
                }
            }
        }

        const workers = Array.from({ length: Math.min(concurrency, files.length) }, worker);
        await Promise.all(workers);
    }

    async function complete(videoId: string, transcodedUploadSessionId: string): Promise<void> {
        const files = state.files
            .filter(file => file.status === "uploaded")
            .map(file => ({
                file_id: file.id,
                relative_path: file.relativePath,
                object_key: file.objectKey,
                size: file.size_bytes,
            }));

        await postJson(apiUrl(videoId, "complete"), { transcoded_upload_session_id: transcodedUploadSessionId, files });
    }

    /** Shared batch/presign/upload loop, used by both `start()` and `resume()`. */
    async function runUploadLoop(): Promise<void> {
        const videoId = state.videoId;
        const transcodedUploadSessionId = state.transcodedUploadSessionId;
        if (!videoId || !transcodedUploadSessionId) {
            throw new Error("Upload session information is missing.");
        }

        stopping = false;
        abortController = new AbortController();
        state.status = "uploading";
        state.error = null;
        startSpeedTracking();

        try {
            for (let start = 0; start < state.files.length; start += batchSize) {
                if (stopping) return;

                const batch = state.files.slice(start, start + batchSize);
                const pendingBatch = batch.filter(file => file.status !== "uploaded");
                if (pendingBatch.length === 0) continue;

                await requestUploadUrls(videoId, transcodedUploadSessionId, pendingBatch);
                await uploadWithWorkerPool(videoId, transcodedUploadSessionId, pendingBatch);

                if (pendingBatch.some(file => file.status === "failed")) {
                    state.status = "failed";
                    state.error = "One or more files failed to upload.";
                    stopSpeedTracking();
                    return;
                }
            }

            if (!stopping) {
                await complete(videoId, transcodedUploadSessionId);
                state.status = "completed";
                stopSpeedTracking();
            }
        } catch (error) {
            if (stopping) return;
            state.status = "failed";
            state.error = error instanceof Error ? error.message : "Upload failed";
            stopSpeedTracking();
        }
    }

    /** Begins a fresh upload. `videoId` / `uploadSessionId` must already exist (see your /new-upload-record step). */
    async function start(files: File[], options: UploadOptions): Promise<void> {
        if (state.status === "uploading") {
            throw new Error("An upload is already running.");
        }

        initializeFiles(files);
        state.videoId = options.videoId;
        state.transcodedUploadSessionId = options.transcodedUploadSessionId;
        batchSize = options.batchSize ?? DEFAULT_BATCH_SIZE;
        concurrency = options.concurrency ?? DEFAULT_CONCURRENCY;
        maxRetries = options.maxRetries ?? DEFAULT_MAX_RETRIES;

        await runUploadLoop();
    }

    function pause(): void {
        if (state.status !== "uploading") return;

        stopping = true;
        abortController?.abort();
        state.status = "paused";
        stopSpeedTracking();

        if (state.videoId && state.transcodedUploadSessionId) {
            postWithQuery(apiUrl(state.videoId, "pause"), { transcoded_upload_session_id: state.transcodedUploadSessionId }).catch(
                error => console.error("Failed to notify backend of pause:", error),
            );
        }
    }

    /**
     * Resumes without resetting progress. The backend doesn't hand back a list of
     * already-uploaded files on /resume -- that reconciliation happens inside
     * requestUploadUrls, via presign-batch's `already_uploaded` flag -- so this
     * just flips the session back to UPLOADING and re-enters the normal loop.
     */
    async function resume(): Promise<void> {
        if (state.status !== "paused") return;
        if (!state.videoId || !state.transcodedUploadSessionId) {
            throw new Error("Upload session information is missing.");
        }

        await postWithQuery(apiUrl(state.videoId, "resume"), { transcoded_upload_session_id: state.transcodedUploadSessionId });
        await runUploadLoop();
    }

    function cancel(): void {
        stopping = true;
        abortController?.abort();

        for (const file of state.files) {
            if (file.status !== "uploaded") file.status = "cancelled";
        }
        state.status = "cancelled";
        stopSpeedTracking();

        if (state.videoId && state.transcodedUploadSessionId) {
            // Note: the backend's abort() is currently unimplemented (`pass`), so
            // this won't actually clean up records server-side yet.
            postWithQuery(apiUrl(state.videoId, "abort"), { transcoded_upload_session_id: state.transcodedUploadSessionId }).catch(
                error => console.error("Failed to notify backend of cancel:", error),
            );
        }
    }

    const uploadedBytes = $derived(
        state.files.reduce((total, file) => total + file.uploadedBytes, 0),
    );

    const progress = $derived.by(() => {
        if (state.totalBytes === 0) return 0;
        return Math.round((uploadedBytes / state.totalBytes) * 100);
    });

    const uploadedFileCount = $derived(
        state.files.filter(file => file.status === "uploaded").length,
    );

    const failedFileCount = $derived(
        state.files.filter(file => file.status === "failed").length,
    );

    return {
        state,
        progress,
        uploadedBytes,
        uploadedFileCount,
        failedFileCount,
        start,
        pause,
        resume,
        cancel,
    };
}
