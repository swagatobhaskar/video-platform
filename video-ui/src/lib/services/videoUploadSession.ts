// Upload workflow + state
import {
    initiateUpload,
    getPresignedUrl,
    uploadChunk,
    completeUpload,
    abortUpload,
    type UploadedPart
} from './multipartUploadService';

import { splitFileIntoChunks } from '$lib/helpers/helpers';

interface UploadState {
    uploading: boolean;
    progress: number;
    speed: number;
    eta: number;
    error: string | null;
}

export function createVideoUploadSession() {
    
    const state: UploadState = {
        uploading: false,
        progress: 0,
        speed: 0,
        eta: 0,
        error: null
    };

    let abortController: AbortController | null = null;

    let currentUploadId: string | null = null;
    let currentKey: string | null = null;

    let totalUploadedBytes = 0;
    let startTime = 0;

    async function upload(file: File) {
        state.uploading = true;
        state.progress = 0;
        state.speed = 0;
        state.eta = 0;
        state.error = null;

        totalUploadedBytes = 0;
        startTime = Date.now();

        abortController = new AbortController();
        const signal = abortController.signal;

        try {
            // STEP 1: Initiate Upload
            const { uploadId, key } = await initiateUpload(
                file.name,
                file.type,
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

                        const elapsedSeconds =
                            (Date.now() - startTime) / 1000;

                        state.speed =
                            totalUploadedBytes / elapsedSeconds;

                        const remainingBytes =
                            file.size - totalUploadedBytes;

                        state.eta =
                            remainingBytes / state.speed;

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
                key,
                file.name,
                uploadId,
                parts,
                signal
            );
        } catch (err: unknown) {
            if (err instanceof Error) {

                if (err.name === "AbortError") {
                    console.log("Upload cancelled");
                } else {
                    state.error = err.message;
                }

            } else {
                state.error = "Unknown upload error";
            }
        } finally {
            state.uploading = false;
            currentUploadId = null;
            currentKey = null;
        }
    }

    async function cancel() {
        abortController?.abort();
        try {
            if (currentUploadId && currentKey) {
                await abortUpload(
                    currentUploadId,
                    currentKey
                );
            }
        } catch (err) {
            console.warn("Abort cleanup failed", err);
        } finally {
            // Reset controllers and trackers
            abortController = null;
            // activeXHR = null;

            // Reset upload session tracking
            currentUploadId = null;
            currentKey = null;

            // Reset state
            state.uploading = false;
            state.progress = 0;
            state.speed = 0;
            state.eta = 0;
        }
    }

    return {
        state,
        upload,
        cancel
    };
}