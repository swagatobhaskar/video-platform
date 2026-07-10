
import {
    initiateUpload,
    getPresignedUrl,
    uploadChunk,
    completeUpload,
    abortUpload,
    type UploadedPart
} from './multipartUploadService';

import { splitFileIntoChunks } from '$lib/helpers/multipartUploadHelper';

export function createVideoUploadSession() {
    // Reactive state (runes)
    const state = $state({
        file: null as File | null,
        uploading: false,
        progress: 0,
        speed: 0,
        eta: 0,
        complete: false,
        error: null as string | null
    });

    let abortController: AbortController | null = null;
    let currentUploadId: string | null = null;
    let currentKey: string | null = null;

    let totalUploadedBytes = 0;
    let startTime = 0;

    async function upload(file: File) {
        state.file = file;
        state.uploading = true;
        state.error = null;
        state.progress = 0;
        state.speed = 0;
        state.eta = 0;
        state.complete = false;

        totalUploadedBytes = 0;
        startTime = Date.now();

        abortController = new AbortController();
        const signal = abortController.signal;

        try {
            // STEP 1: Initiate Upload
            const { uploadId, key, videoId } = await initiateUpload(
                file.name,
                file.type,
                file.size,
                signal
            );
            
            currentUploadId = uploadId;
            currentKey = key;

            const chunks = splitFileIntoChunks(file);
            const parts: UploadedPart[] = [];

            // STEP 2-3: Upload Parts
            for (let i = 0; i < chunks.length; i++) {
                const partNumber = i + 1;

                const uploadUrl = await getPresignedUrl(
                    uploadId,
                    key,
                    partNumber,
                    signal
                );

                let previousLoaded = 0;

                const etag = await uploadChunk(
                    uploadUrl,
                    chunks[i],
                    (loaded) => {
                        const delta = loaded - previousLoaded;
                        previousLoaded = loaded;
                        totalUploadedBytes += delta;

                        const elapsedSeconds = (Date.now() - startTime) / 1000;

                        state.speed = elapsedSeconds > 0 ? ( totalUploadedBytes / elapsedSeconds ) : 0;

                        const remainingBytes = file.size - totalUploadedBytes;

                        state.eta = state.speed > 0 ? (remainingBytes / state.speed) : 0;

                        state.progress = Math.round(
                            (totalUploadedBytes / file.size) * 100
                        );
                    },
                    signal
                );

                parts.push({
                    ETag: etag,
                    PartNumber: partNumber
                });
            }

            // Step 4: Complete Upload
            await completeUpload(
                currentKey!,
                file.name,
                currentUploadId!,
                parts,
                videoId,
                signal
            );
        } catch (err: unknown) {
            if (err instanceof Error) {
                if (err.name === "AbortError") {
                    console.log("Upload cancelled");
                } else {
                    console.error(err);
                    state.error = err.message;
                }
            } else {
                console.error(err);
                state.error = 'Unknown error occurred';
            }
        } finally {
            state.uploading = false;
            currentUploadId = null;
            currentKey = null;
            state.complete = true;
        }
    }

    async function cancel() {
        // Cancel in-flight requests
        abortController?.abort();

        try {
            if (currentUploadId && currentKey) {
                await abortUpload(currentUploadId, currentKey);
            }
        } catch (err) {
            console.warn("Abort cleanup failed", err);
        } finally {
            state.uploading = false;

            // Reset controllers and trackers
            abortController = null;

            // Reset upload session tracking
            currentUploadId = null;
            currentKey = null;

            // reset metrics
            state.progress = 0;
            state.speed = 0;
            state.eta = 0;

            totalUploadedBytes = 0;
            startTime = 0;
        }
    }

    return {
        state,
        upload,
        cancel
    };
}
