// Only API Communication
import { uploadChunkWithProgress } from "$lib/helpers/multipartUploadHelper";

const API_BASE = "http://127.0.0.1:8000/api/video/uploads";

export interface UploadedPart {
    ETag: string | null;
    PartNumber: number;
}

export async function initiateUpload(
    fileName: string,
    contentType: string,
    fileSizeBytes: number,
    // uploadSessionId: string,
    // totalParts: number,
    signal?: AbortSignal
): Promise<{ uploadId: string; key: string, uploadSessionId: string, videoId: string }> {
    
    // Get the uploadSessionId from cookies
    const uploadSessionId = await cookieStore.get("uploadSessionId");

    const res = await fetch(`${API_BASE}/initiate-upload/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            fileName: fileName,
            contentType: contentType,
            fileSizeBytes: fileSizeBytes,
            uploadSessionId: uploadSessionId?.value,
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
    signal?: AbortSignal
): Promise<string> {
    const res = await fetch(`${API_BASE}/get-presigned-url`, {
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


export async function completeUpload(
    key: string,
    filename: string,
    uploadId: string,
    parts: UploadedPart[],
    videoId?: string,
    signal?: AbortSignal
): Promise<void> {

    const uploadSessionCookie = await cookieStore.get("uploadSessionId");
    const uploadSessionId = uploadSessionCookie?.value;

    // console.log("COOKIE Upload session ID: ", uploadSessionId); // working

    const res = await fetch(`${API_BASE}/complete-upload`, {
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
        }),
        signal
    });

    if (!res.ok) {
        throw new Error("Failed to complete upload");
    }
}


export async function abortUpload(
    uploadId: string,
    key: string
): Promise<void> {
    await fetch(`${API_BASE}/abort-upload`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            uploadId,
            key
        })
    });
}
