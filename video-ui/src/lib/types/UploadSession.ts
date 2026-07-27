
export type UploadSessionStatus =
    | "pending"
    | "uploading"
    | "paused"
    | "completed"
    | "failed"
    | "aborted";

export type UploadSession = {
    id: string;
    video_id: string | null;
    object_key: string | null;
    video_upload_id: string | null;
    file_size_bytes: number | null;
    mime_type: string | null;
    original_filename: string | null;
    total_parts: number | null;
    uploaded_parts_count: number;
    status: UploadSessionStatus;
    created_at: string;
    updated_at: string;
    completed_at: string | null;
};
