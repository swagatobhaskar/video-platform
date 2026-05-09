
export type UploadWorkflowStep =
    | "idle"
    | "upload-video"
    | "video-uploading"
    | "video-processing"
    | "upload-thumbnail"
    | "editing-metadata"
    | "ready-to-publish"
    | "publishing"
    | "published"
    | "failed";

export function createUploadWorkflowController() {
    let currentStep = $state<UploadWorkflowStep>("idle");

    function goToStep(step: UploadWorkflowStep) {
        currentStep = step;
    }

    function resetStep() {
        currentStep = "idle";
    }

    return {
        get currentStep() {
            return currentStep;
        },
        goToStep,
        resetStep
    }
}