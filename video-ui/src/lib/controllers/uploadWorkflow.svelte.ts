
export type workflowSubStep =
    | "idle"
    | "video-upload"
    | "video-uploading"
    | "video-processing"
    | "upload-thumbnail"
    | "editing-metadata"
    | "ready-to-publish"
    | "publishing"
    | "published"
    | "failed";

type LayoutState = 
    | "video-drop"
    | "upload-dashboard"
    | "ready-to-publish"
    | "publishing"
    | "published"
    | "draft"
    | "error";

export function createUploadWorkflowController() {
    let currentStep = $state<LayoutState>("video-drop");

    const workflowProgress = $state({
        videoUploaded: false,
        videoProcessing: false,
        thumbnailUploaded: false,
        metadataFilled: false,
        readyToPublish: false,
        publishing: false,
        published: false,
        failed: false,
        draft: true,
    });

    const videoSessionId: string | null = $state(null);

    function goToStep(step: LayoutState) {
        currentStep = step;
    }

    function resetStep() {
        currentStep = "video-drop";
    }

    return {
        get currentStep() {
            return currentStep;
        },
        goToStep,
        resetStep,
        workflowProgress,
        videoSessionId,
    }
}