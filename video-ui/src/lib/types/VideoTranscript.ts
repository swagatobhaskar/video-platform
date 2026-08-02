export type VideoTranscript = {
    id: string;
    language_code: 'en' | 'hi' | 'bn';
    transcript_text: string | null;
    video_id: string;
    created_at: string;
    updated_at: string;
}
