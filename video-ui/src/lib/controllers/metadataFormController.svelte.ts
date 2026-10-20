
type MetadataFields = {
    title: string,
    description: string,
    category: string,
    language: "hindi" | "bengali",
    series: string | number,
    episode_number: number | null,
    transcript: string,
    transcript_code: "bn" | "hi",
    seo_tags: string[],  // make it 'keywords'
    publication_status: "draft" | "published",
    meta_title: string,
    meta_description: string,
    thumbnail_alt_text: string,
    seo_summary_en: string,
    focus_keywords: string[],
    secondary_keywords: string[],
}

export function MetadataFormController() {
    /**
     * Responsibilities:
     * 1. Auto-save
     * 2. Ensure every field is filled
     * 3. Validation
     */

    const formData = $state<MetadataFields>({
        title: '',
        description: '',
        category: '',
        language: 'bengali',
        series: '',
        episode_number: null,
        transcript: '',
        transcript_code: 'bn',
        seo_tags: [''],
        focus_keywords: [''],
        secondary_keywords: [''],
        publication_status: "draft",
        meta_title: '',
        meta_description: '',
        thumbnail_alt_text: '',
        seo_summary_en: '',
    });

    function populate(data: Partial<MetadataFields> & Record<string, unknown>) {
    // This ensures that any incoming keys match the known fields of MetadataFields,
    // while still allowing optional or extra API properties if needed.
        Object.assign(formData, {
            ...data,
            meta_title: data.meta_title ?? data.title ?? '',
            meta_description: data.meta_description ?? data.description ?? '',
        });
    }

    return {
        formData,
        populate,
    }
}