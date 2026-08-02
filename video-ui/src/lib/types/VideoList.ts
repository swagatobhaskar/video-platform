export type VideoList = {
    id: string;
    title: string;
    slug: string | null;
    publication_status: string;
    created_at: Date;
    updated_at: Date;
    object_key: string | null;
}