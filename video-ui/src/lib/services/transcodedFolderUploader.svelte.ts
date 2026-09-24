export function uploadFileWithProgress(
    file: File,
    uploadUrl: string,
    onProgress: (uploadedBytes: number) => void,
): Promise<void> {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.open("PUT", uploadUrl);

        xhr.setRequestHeader(
            "Content-Type",
            file.type || "application/octet-stream",
        );

        xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
                onProgress(event.loaded);
            }
        };

        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                onProgress(file.size);
                resolve();
            } else {
                reject(
                    new Error(`Upload failed: HTTP ${xhr.status}`)
                );
            }
        };

        xhr.onerror = () => {
            reject(new Error("Network error while uploading file"));
        };

        xhr.onabort = () => {
            reject(new Error("Upload aborted"));
        };

        xhr.send(file);
    });
}

type UploadFile = {
    id: string;
    file: File;
    relativePath: string;

    uploadUrl?: string;
    objectKey?: string;

    uploadedBytes: number;
    uploaded: boolean;
};

function createUploadFiles(files: File[]): UploadFile[] {
    return files.map((file) => ({
        id: crypto.randomUUID(),
        file,
        relativePath: file.webkitRelativePath || file.name,
        uploadedBytes: 0,
        uploaded: false,
    }));
}

async function getUploadUrls(
    videoId: string,
    uploadSessionId: string,
    files: UploadFile[],
) {
    const response = await fetch(
        `/api/video/${videoId}/transcoded/upload-urls`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                upload_session_id: uploadSessionId,

                files: files.map((item) => ({
                    file_id: item.id,
                    relative_path: item.relativePath,
                    size: item.file.size,
                    content_type:
                        item.file.type || "application/octet-stream",
                })),
            }),
        },
    );

    if (!response.ok) {
        throw new Error("Failed to get upload URLs");
    }

    return await response.json();
}

function applyUploadUrls(
    files: UploadFile[],
    response: {
        files: {
            file_id: string;
            object_key: string;
            upload_url: string;
        }[];
    },
) {
    for (const item of response.files) {
        const file = files.find(
            (file) => file.id === item.file_id,
        );

        if (!file) {
            continue;
        }

        file.uploadUrl = item.upload_url;
        file.objectKey = item.object_key;
    }
}

async function uploadBatch(
    files: UploadFile[],
    onProgress: () => void,
) {
    await Promise.all(
        files.map(async (item) => {
            if (!item.uploadUrl) {
                throw new Error(
                    `No upload URL for ${item.relativePath}`,
                );
            }

            await uploadFileWithProgress(
                item.file,
                item.uploadUrl,
                (uploadedBytes) => {
                    item.uploadedBytes = uploadedBytes;
                    onProgress();
                },
            );

            item.uploaded = true;
        }),
    );
}

export async function uploadTranscodedFolder(
    files: File[],
    videoId: string,
    uploadSessionId: string,
) {
    const uploadFiles = createUploadFiles(files);

    const batchSize = 10;

    let uploadedBytes = 0;

    function updateProgress() {
        uploadedBytes = uploadFiles.reduce(
            (total, file) => total + file.uploadedBytes,
            0,
        );

        const totalBytes = uploadFiles.reduce(
            (total, file) => total + file.file.size,
            0,
        );

        const progress =
            totalBytes === 0
                ? 0
                : (uploadedBytes / totalBytes) * 100;

        console.log(`${progress.toFixed(1)}%`);
    }

    for (
        let i = 0;
        i < uploadFiles.length;
        i += batchSize
    ) {
        const batch = uploadFiles.slice(
            i,
            i + batchSize,
        );

        console.log(
            `Uploading files ${i + 1} - ${i + batch.length}`,
        );

        // 1. Get presigned URLs
        const response = await getUploadUrls(
            videoId,
            uploadSessionId,
            batch,
        );

        // 2. Attach URLs to our files
        applyUploadUrls(batch, response);

        // 3. Upload the batch concurrently
        await uploadBatch(
            batch,
            updateProgress,
        );

        // 4. Tell backend which files succeeded
        for (const file of batch) {
            await recordUploadedFile(
                videoId,
                uploadSessionId,
                file,
            );
        }
    }

    console.log("All files uploaded");

    await completeUpload(
        videoId,
        uploadSessionId,
    );
}

async function recordUploadedFile(
    videoId: string,
    uploadSessionId: string,
    file: UploadFile,
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
                file_id: file.id,
                relative_path: file.relativePath,
                object_key: file.objectKey,
                size: file.file.size,
            }),
        },
    );

    if (!response.ok) {
        throw new Error(
            `Failed to record ${file.relativePath}`,
        );
    }
}

async function completeUpload(
    videoId: string,
    uploadSessionId: string,
) {
    const response = await fetch(
        `/api/video/${videoId}/transcoded/complete`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                upload_session_id: uploadSessionId,
            }),
        },
    );

    if (!response.ok) {
        throw new Error("Failed to complete upload");
    }
}
