export type VideoList = {
    id: string;
    title: string;
    slug: string | null;
    publication_status: string;
    published_at: Date | null;
    created_at: Date;
    updated_at: Date;
    object_key: string | null;
    thumbnail_object_key: string | null;
}