const API = "http://localhost:8000";

export async function uploadVideoFolder(
    files: File[],
    onProgress?: (uploaded: number, total: number) => void
) {
    const form = new FormData();

    for (const file of files) {
        form.append("files", file, file.webkitRelativePath || file.name);
    }

    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable && onProgress) {
                onProgress(e.loaded, e.total);
            }
        };

        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve(JSON.parse(xhr.responseText));
            } else {
                reject(xhr.responseText);
            }
        };

        xhr.onerror = reject;
        xhr.open("POST", `${API}/upload-folder`);
        xhr.send(form);
    });
}
