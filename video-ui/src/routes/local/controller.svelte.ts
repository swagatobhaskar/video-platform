import { uploadVideoFolder } from "./services";

export function UploadController() {

    const state = $state({
        selectedFiles: null as File[] | null, // [],
        uploading: false,
        progress: 0,
        error: null as string | null, // "",
        success: null as string | null, // "",
    });

    // let selectedFiles = $state<File[]>([]);
    // let uploading = $state(false);
    // let progress = $state(0);
    // let error = $state("");
    // let success = $state("");

    async function setFiles(files: File[]) {
        state.error = null;
        state.success = null;

        if (!files.length) {
            return;
        }

        console.log("All files selected:", files);

        const manifest = files.find( f => f.webkitRelativePath.endsWith("dash/manifest.mpd"));

        if (!manifest) {
            state.error = "No dash/manifest.mpd found.";
            return;
        }

        state.selectedFiles = files;
    }

    async function upload() {

        if (!state.selectedFiles?.length) {
            return;
        }

        state.uploading = true;

        try {
            await uploadVideoFolder(
                state.selectedFiles,
                (uploaded, total) => {
                    state.progress = Math.round(uploaded / total * 100);
                }
            );

            state.success = "Upload Complete.";
        } catch (e) {
            state.error = String(e);
        } finally {
            state.uploading = false;
        }
    }

    return {
        setFiles,
        upload,
        state,
    }
}
