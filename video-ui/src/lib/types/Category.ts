type Video = {
    id: string;
    title: string;
    thumbnail_object_key: string;
}

export type Category = {
    id: string;
    name: string;
    created_at: string;
    updated_at: string;
    r2_category_image_key: string | null;
    videos: [Video];
}