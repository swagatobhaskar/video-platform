// Only API Communication
import { uploadChunkWithProgress } from "$lib/helpers/multipartUploadHelper";

const API_BASE = "http://127.0.0.1:8000/api/video/upload";

export interface UploadedPart {
    ETag: string;
    PartNumber: number;
    SizeBytes: number;
}

export async function initiateUpload(
    fileName: string,
    contentType: string,
    fileSizeBytes: number,
    videoId: string,
    uploadSessionId: string,
    // totalParts: number,
    signal?: AbortSignal
): Promise<{ uploadId: string; key: string, uploadSessionId: string, videoId: string }> {
    
    const res = await fetch(`${API_BASE}/${videoId}/initiate-upload/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            fileName: fileName,
            contentType: contentType,
            fileSizeBytes: fileSizeBytes,
            uploadSessionId: uploadSessionId,
            // totalParts: totalParts,
        }),
        signal
    });
    
    if (!res.ok) {
        throw new Error(`Upload Initiation Failed: ${res.status}`);
    }

    return res.json();
}


export async function getPresignedUrl(
    uploadId: string,
    key: string,
    partNumber: number,
    videoId: string,
    signal?: AbortSignal
): Promise<string> {
    const res = await fetch(`${API_BASE}/${videoId}/get-presigned-url`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            uploadId,
            key,
            partNumber
        }),
        signal
    });

    if (!res.ok) {
        throw new Error(`Failed to get URL for part ${partNumber}`);
    }

    const data = await res.json();

    if (!data.uploadUrl) {
        throw new Error(`Missing upload URL for part ${partNumber}`);
    }

    return data.uploadUrl;
}


export async function uploadChunk(
    uploadUrl: string,
    chunk: Blob,
    onProgress: (loaded: number) => void,
    signal: AbortSignal
): Promise<string | null> {
    const { etag } = await uploadChunkWithProgress(
        uploadUrl,
        chunk,
        onProgress,
        signal
    );

    return etag;
}

export async function recordUploadedPart(
    uploadId: string,
    videoId: string,
    part: UploadedPart,
    signal?: AbortSignal,
): Promise<void> {
    const res = await fetch(`${API_BASE}/${uploadId}/video/${videoId}/record-uploaded-part`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(part),
            signal,
        }
    );

    if (!res.ok) {
        throw new Error(`Failed to record uploaded part ${part.PartNumber}: ${res.status}`)
    }
}


export async function completeUpload(
    key: string,
    filename: string,
    uploadId: string,
    parts: UploadedPart[],
    videoId: string,
    uploadSessionId: string,
    signal?: AbortSignal
): Promise<void> {
    const res = await fetch(`${API_BASE}/${videoId}/complete-upload`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            key,
            filename,
            uploadId,
            parts,
            uploadSessionId,
            // videoId, passing it via url
        }),
        signal
    });

    if (!res.ok) {
        throw new Error("Failed to complete upload");
    }
}


export async function abortUpload(
    uploadId: string,
    key: string,
    videoId: string,
): Promise<void> {
    await fetch(`${API_BASE}/${videoId}/abort-upload`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            uploadId,
            key,
            videoId,
        })
    });
}

export async function pauseUpload(
    videoId: string,
    uploadId: string,
): Promise<{ success: boolean, status: string }> {
    const res = await fetch(`${API_BASE}/${uploadId}/video/${videoId}/pause-upload`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            videoId,
            uploadId,
        })
    });

    if (!res.ok) {
        throw new Error("Failed to pause upload");
    }

    const { success, status } = await res.json();

    return { success, status };
}


export async function resumeUpload(
    videoId: string,
    uploadId: string,
): Promise<{ success: boolean, status: string, uploadedParts: UploadedPart[] }> {
    const res = await fetch(`${API_BASE}/${uploadId}/video/${videoId}/resume-upload`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            videoId,
            uploadId,
        })
    });

    if (!res.ok) {
        throw new Error("Failed to resume upload");
    }

    const { success, status, uploadedParts } = await res.json();

    return { success, status, uploadedParts };
}
