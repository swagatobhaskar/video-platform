type Video = {
    id: string;
    title: string;
    thumbnail_object_key: string;
}

export type Series = {
    id: string;
    name: string;
    created_at: string;
    updated_at: string;
    videos: Video[];
}