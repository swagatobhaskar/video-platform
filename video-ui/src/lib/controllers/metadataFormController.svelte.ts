
type MetadataFields = {
    title: string,
    description: string,
    category: string,
    seoTags: string[],   
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
        seoTags: [''], 
    });

    return {
        formData,
    }
}