import { SvelteSet } from 'svelte/reactivity';

import {
    initiateUpload,
    getPresignedUrl,
    uploadChunk,
    completeUpload,
    abortUpload,
    pauseUpload,
    resumeUpload,
    type UploadedPart,
    recordUploadedPart
} from './multipartUploadService';

import { splitFileIntoChunks } from '$lib/helpers/multipartUploadHelper';

export function createVideoUploadSession() {
    // Reactive state (runes)
    const state = $state({
        file: null as File | null,
        
        uploading: false,
        paused: false,
        pausing: false,
        resuming: false,
        
        progress: 0,
        speed: 0,
        eta: 0,

        complete: false,
        error: null as string | null,
    });

    // -------------------------------------------
    // Internal upload state
    // -------------------------------------------
    
    let abortController: AbortController | null = null;
    let currentUploadId: string | null = null;
    let currentKey: string | null = null;
    let currentVideoId: string | null = null;
    let currentUploadSessionId: string | null = null;
    
    let pauseRequested = false;    
    let totalUploadedBytes = 0;
    let startTime = 0;

    // -------------------------------------------
    // Main upload
    // -------------------------------------------

    async function upload(file: File, videoId: string, uploadSessionId: string) {
        if (!videoId || !uploadSessionId) {
            throw new Error("Missing videoId or uploadSessionId.");
        }

        state.file = file;
        state.uploading = true;
        state.paused = false;
        state.error = null;
        state.progress = 0;
        state.speed = 0;
        state.eta = 0;
        state.complete = false;

        totalUploadedBytes = 0;
        startTime = Date.now();

        currentVideoId = videoId;
        currentUploadSessionId = uploadSessionId;

        pauseRequested = false;
        abortController = new AbortController();
        // const signal = abortController.signal;

        try {
            // STEP 1: Initiate Upload
            const { uploadId, key } = await initiateUpload(
                file.name,
                file.type,
                file.size,
                videoId,
                currentUploadSessionId,
                abortController.signal  // signal
            );
            
            currentUploadId = uploadId;
            currentKey = key;

            const chunks = splitFileIntoChunks(file);
            const parts: UploadedPart[] = [];

            // STEP 2-3: Upload Parts
            // for (let i = 0; i < chunks.length; i++) {
            //     const chunk = chunks[i];
            //     const partNumber = i + 1;

            //     const uploadUrl = await getPresignedUrl(
            //         uploadId,
            //         key,
            //         partNumber,
            //         videoId,
            //         abortController.signal
            //     );

            //     let previousLoaded = 0;

            //     const etag = await uploadChunk(
            //         uploadUrl,
            //         chunks[i],
            //         (loaded) => {
            //             const delta = loaded - previousLoaded;
            //             previousLoaded = loaded;
            //             totalUploadedBytes += delta;

            //             const elapsedSeconds = (Date.now() - startTime) / 1000;

            //             state.speed = elapsedSeconds > 0 ? ( totalUploadedBytes / elapsedSeconds ) : 0;

            //             const remainingBytes = file.size - totalUploadedBytes;

            //             state.eta = state.speed > 0 ? (remainingBytes / state.speed) : 0;

            //             state.progress = Math.round(
            //                 (totalUploadedBytes / file.size) * 100
            //             );
            //         },
            //         abortController.signal
            //     );

            //     if (!etag) {
            //         throw new Error(`Missing ETag for part ${partNumber}`);
            //     }

            //     await recordUploadedPart(
            //         currentUploadId,
            //         currentVideoId,
            //         {
            //             ETag: etag,
            //             PartNumber: partNumber,
            //             SizeBytes: chunk.size,
            //         },
            //         abortController.signal
            //     );

            //     parts.push({
            //         ETag: etag,
            //         PartNumber: partNumber,
            //         SizeBytes: chunk.size,
            //     });
            // }

            await uploadParts(
                chunks,
                parts,
                new SvelteSet<number>()
            );

            if (pauseRequested) {
                return;
            }

            // Step 4: Complete Upload
            await completeUpload(
                currentKey!,
                file.name,
                currentUploadId!,
                parts,
                videoId,
                currentUploadSessionId,
                abortController.signal
            );

            state.complete = true;
            state.uploading = false;

        } catch (err) {
            // if (err instanceof Error && err.name === "AbortError") {
            //     console.log("Upload pause requested");
            if (pauseRequested) {
                console.log("Upload pause requested");

                try {
                    await pauseUpload(currentVideoId!, currentUploadId!);
                    state.uploading = false;
                    state.paused = true;
                    state.error = null;

                } catch (pauseErr) {
                    console.error("Failed to pause upload:", pauseErr);
                    state.error = pauseErr instanceof Error ? pauseErr.message : "Failed to pause upload";
                    pauseRequested = false;
                } finally {
                    state.pausing = false;
                }

                return;
            }

            // Actual cancellation
            // return;
            if (err instanceof Error && err.name === "AbortError") {
                    console.log("Upload cancelled");
                    return;
                }
            // }

            state.error = err instanceof Error ? err.message : "Unknown error occurred";
            state.uploading = false;
        }
    }

    // --------------------------------------------------
    // Multipart part uploading
    // --------------------------------------------------

    async function uploadParts(chunks: Blob[], parts: UploadedPart[], uploadedPartNumbers: Set<number>) {
        for (let i = 0; i < chunks.length; i++) {
            const chunk = chunks[i];
            const partNumber = i + 1;

            if (uploadedPartNumbers.has(partNumber)) {
                continue;
            }

            const uploadUrl = await getPresignedUrl(
                currentUploadId!,
                currentKey!,
                partNumber,
                currentVideoId!,
                abortController!.signal
            );

            let previousLoaded = 0;

            const etag = await uploadChunk(
                uploadUrl,
                chunk,
                (loaded) => {
                    const delta = loaded - previousLoaded;
                    previousLoaded = loaded;
                    totalUploadedBytes += delta;

                    const elapsedSeconds = (Date.now() - startTime) / 1000;

                    state.speed = elapsedSeconds > 0 ? ( totalUploadedBytes / elapsedSeconds ) : 0;

                    const remainingBytes = state.file!.size - totalUploadedBytes;

                    state.eta = state.speed > 0 ? (remainingBytes / state.speed) : 0;

                    state.progress = Math.round(
                        (totalUploadedBytes / state.file!.size) * 100
                    );
                },
                abortController!.signal
            );

            if (!etag) {
                throw new Error(`Missing ETag for part ${partNumber}`);
            }

            const uploadedPart = {
                ETag: etag,
                PartNumber: partNumber,
                SizeBytes: chunk.size
            };

            await recordUploadedPart(
                currentUploadId!,
                currentVideoId!,
                uploadedPart,
                abortController!.signal
            );

            parts.push(uploadedPart);
            uploadedPartNumbers.add(partNumber);
        }
    }

    // --------------------------------------------------
    // Pause / Resume
    // --------------------------------------------------

    async function pause() {
        console.log("Pause requested");

        if (!currentUploadId || !currentVideoId) {
            return;
        }

        if (!state.uploading || state.paused || state.pausing) {
            return;
        }

        state.pausing = true;
        pauseRequested = true;

        console.log("Aborting current request...");

        // Stop the currently running HTTP request.
        abortController?.abort();

        // Do NOT call pauseUpload() here yet.
        // move the backend pause call into the AbortError branch of upload().

        // try {
        //     await pauseUpload(currentVideoId, currentUploadId);
        //     state.paused = true;
        //     state.uploading = false;
        // } catch (err) {
        //     state.error = err instanceof Error ? err.message : "Failed to pause upload";
        //     pauseRequested = false;
        // } finally {
        //     state.pausing = false;
        // }
    }

    async function resume() {
        console.log("Inside Resume Service.");

        if (!currentUploadId || !currentVideoId || !state.file || !currentUploadSessionId) {
            console.log("2. Missing upload state");
            return;
        }

        if (!state.paused) {
            console.log("3. Not paused");
            return;
        }

        state.resuming = true;
        state.error = null;

        try {
            console.log("4. Calling resumeUpload()");
            const response = await resumeUpload(currentVideoId, currentUploadId);
            console.log("5. Response from resume-upload: ", response);

            const uploadedParts: UploadedPart[] = response.uploadedParts;
            console.log("6. Uploaded parts:", uploadedParts);

            const chunks = splitFileIntoChunks(state.file);
            console.log("7. Chunks:", chunks.length);

            const uploadedPartNumbers = new SvelteSet<number>(uploadedParts.map((part: UploadedPart) => part.PartNumber));
            console.log("8. Uploaded part numbers:", [...uploadedPartNumbers]);

            // Reconstruct progress from parts
            totalUploadedBytes = uploadedParts.reduce((total, part) => total + part.SizeBytes, 0);
            state.progress = Math.round((totalUploadedBytes / state.file.size) * 100);
            console.log("9. Progress:", state.progress);

            pauseRequested = false;
            abortController = new AbortController();

            state.paused = false;
            state.uploading = true;

            console.log("10. Calling uploadParts()");
            await uploadParts(chunks, uploadedParts, uploadedPartNumbers);
            console.log("11. uploadParts() finished");

            // make sure the array is sorted before completin.
            // S3's CompleteMultipartUpload expects the parts in ascending PartNumber order.
            const sortedUploadedParts = uploadedParts.sort((a, b) => a.PartNumber - b.PartNumber);
            console.log("12. Sorted parts:", sortedUploadedParts);

            await completeUpload(
                currentKey!,
                state.file.name,
                currentUploadId!,
                // uploadedParts,
                sortedUploadedParts,
                currentVideoId!,
                currentUploadSessionId!,
                abortController.signal
            );
            console.log("14. completeUpload() finished");

            state.complete = true;
            state.uploading = false;
            // state.paused = false;
        } catch (err) {
            console.error("RESUME ERROR:", err);
            state.error = err instanceof Error ? err.message : "Failed to resume upload";
            state.uploading = false;
        } finally {
            console.log("15. Resume finally");
            state.resuming = false;
        }
    }

    // --------------------------------------------------
    // Cancel
    // --------------------------------------------------

    async function cancel() {
        // Capture everything BEFORE aborting the upload
        const uploadId = currentUploadId;
        const key = currentKey;
        const videoId = currentVideoId;
        
        // Cancel in-flight requests
        abortController?.abort();

        try {
            if (uploadId && key && videoId) {
                await abortUpload(uploadId, key, videoId);
            }
        } catch (err) {
            console.warn("Abort cleanup failed", err);
        } finally {
            state.uploading = false;
            state.paused = false;
            state.pausing = false;
            state.resuming = false;

            // Reset controllers and trackers
            abortController = null;

            // Reset upload session tracking
            currentVideoId = null;
            currentUploadId = null;
            currentKey = null;
            currentUploadSessionId = null;

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
        pause,
        resume,
        cancel,
    };
}
