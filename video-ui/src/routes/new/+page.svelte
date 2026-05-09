<script lang="ts">

    import VideoDrop from "./VideoDrop.svelte";
    
    // Video file selection handler
    // let videoFileInputEl = $state<HTMLInputElement | null>(null);

    // function openVideoFileDialog() {
    //     videoFileInputEl?.click();
    // }

    // import { fileInputController } from "$lib/controllers/ui/fileInputController.svelte";
    // const videoInput = fileInputController({uploadFileType: "video"});
    
    // let videoPreviewUrl: string | null = $state(null);
    
    // $effect(() => {
    //     const videoFile = videoInput.state.selectedFile;
    //     if (!videoFile) {
    //         videoPreviewUrl = null;
    //         return;
    //     };
    //     const url = URL.createObjectURL(videoFile);
    //     videoPreviewUrl = url;
        
    //     // clean-up when file changes
    //     return () => URL.revokeObjectURL(url);
    // })
 
</script>

<VideoDrop />


