from fastapi import HTTPException
from pathlib import Path
from botocore.exceptions import ClientError, BotoCoreError
import os
from tempfile import TemporaryDirectory
import logging

from .utils import probe_video, generate_renditions, create_output_directories, build_ffmpeg_command
from app.celery_worker import celery
from app.utils.r2_helper import s3
    
logger = logging.getLogger(__name__)

#
# Helper function to download mp4 files from Cloudflare R2 bucket
#
def download_from_r2(file_name: str, local_download_path: str):
    
    RAW_VIDEO_BUCKET: str = 'raw-video-upload-bucket'
    
    try:
        s3.download_file(
            RAW_VIDEO_BUCKET,
            file_name,
            local_download_path
        )
    
    except ClientError as e:
        code = e.response["Error"]["Code"]

        if code == "NoSuchKey":
            raise HTTPException(
                status_code=404,
                detail="Video not found"
            )

        raise HTTPException(
            status_code=500,
            detail=f"R2 download failed: {code}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

#
# Helper function to upload .mpd, .m3u8, and .m4s chunks to Cloudflare R2 bucket
#
def upload_output_directory_to_r2_bucket(
    local_dir: str | Path,
    video_file_name: str,
):
    
    BUCKET: str = 'processed-videos-bucket'
        
    local_dir = Path(local_dir)
    remote_prefix = Path(video_file_name).stem
    
    failed = []
    
    for file_path in local_dir.rglob("*"):
        if not file_path.is_file():
            continue
    
        key = f"{remote_prefix}/{file_path.relative_to(local_dir)}".replace("\\", "/")
    
        try:
            s3.upload_file(
                str(file_path),
                BUCKET,
                key,
            )
    
        except Exception as e:
            failed.append(
                {
                    "file": str(file_path),
                    "key": key,
                    "error": str(e),
                }
            )
    
    return failed

#
# Transcode helper function.
# 
def transcode_video(video: Path, probe_result: dict, output_dir: Path, dash_dir: Path):
    
    import subprocess
        
    # generate renditions
    renditions = generate_renditions(
        probe_result["height"]
    )
    
    # Create directories
    create_output_directories(
        OUTPUT_ROOT=output_dir
    )

    cmd = build_ffmpeg_command(
        input_file=str(video),
        output_dir=dash_dir,
        renditions=renditions,
        fps=probe_result["fps"]
    )
    
    # Execute FFmpeg
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    
    # Log FFmpeg stdout and stderr
    if result.stdout:
        logger.info("FFmpeg stdout:\n%s", result.stdout)
    if result.stderr:
        logger.info("FFmpeg stderr:\n%s", result.stderr)
        
    # Raise if FFmpeg failed
    result.check_returncode()
     
    # NOT REQUIRD HERE
    # # Delete original uploaded file. After result.check_returncode()
    # try:
    #     os.remove(local_download_path)
    #     logger.info("Deleted source file: %s", local_download_path)
    # except Exception as e:
    #     logger.warning("Failed to delete source file: %s", e)
    
    return {
        "status": "completed",
        # "input": str(video),
        # "output": str(manifest_path),
        "manifest": str(dash_dir / "manifest.mpd"),
        "hls_master": str(dash_dir / "master.m3u8"),
        "metadata": probe_result,
    }
    
"""
@celery.task(
    bind=True,
    # for long tasks
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    )
def process_video_worker_operations(self, file_name: str):
    
    print("INSIDE PROCESS_VIDEO_WORKER_OPERATIONS TASK FUNCTION.")
    
    self.update_state(
        state="DOWNLOADING",
        meta={"step": "downloading"}
    )
    
    # Download the file from R2 to local storage.
    local_download_path = f"/tmp/{Path(file_name)}" # f"/tmp/{Path(file_path).name}"
    download_from_r2(file_name, local_download_path)

    video = Path(local_download_path)

    # Use the stem (filename without extension) as the folder name
    output_dir = video.parent / "processed" / video.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Now you can use output_dir to store DASH/HLS segments
    # Example:
    dash_dir = output_dir / "dash"
    dash_dir.mkdir(parents=True, exist_ok=True)
        
    # output_file = output_dir / f"{video.stem}.mp4"
    # manifest_path = output_dir / "dash" / "manifest.mpd"

    # Celery task state
    self.update_state(
        state="PROBING",
        meta={"step": "ffprobe"}
    )
    
    video = Path(local_download_path)
    
    # ffprobe
    probe_result = probe_video(str(video))
    
    self.update_state(
        state="TRANSCODING",
        meta={"step": "ffmpeg"}
    )
    
    transcode_video(video, probe_result, output_dir, dash_dir)
    
    # Celery task state: Upload processed files
    self.update_state(
        state="UPLOADING",
        meta={"step": "uploading"}
    )

    upload_errors = upload_output_directory_to_r2_bucket(
        local_dir=output_dir,
        video_file_name=video.stem,
    )
    
    if upload_errors:
        logger.error("Errors occurred during upload: %s", upload_errors)
        raise RuntimeError(
            f"{len(upload_errors)} files failed to upload"
        )
    
    # Celery task state: Clean up
    self.update_state(
        state="CLEANUP",
        meta={"step": "cleanup"}
    )
    
    # 1. Delete local tmp files: downloaded video as well as processed video segments and manifests
    # 2. Remove the actual video from R2 bucket (optional, depending on your retention needs)
    try:
        # Delete local output directory (processed segments and manifests)
        if output_dir.exists():
            for item in output_dir.rglob("*"):
                if item.is_file():
                    item.unlink()
            output_dir.rmdir()
            logger.info("Deleted local output directory: %s", output_dir)

        # Delete the downloaded source video
        if video.exists():
            video.unlink()
            logger.info("Deleted local source video: %s", video)

        # Optionally, delete the original uploaded file from R2
        # s3.delete_object(Bucket=RAW_VIDEO_BUCKET, Key=file_name)
        # logger.info("Deleted source file from R2: %s", file_name)

    except Exception as e:
        logger.warning("Cleanup failed: %s", e)
"""

@celery.task(
    bind=True,
    # for long tasks
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    )
def process_video_worker_operations(self, file_name: str):
    
    with TemporaryDirectory(prefix="transcode_") as temp_dir:
        
        temp_dir = Path(temp_dir)
        
        # Celery task state
        self.update_state(
            state="DOWNLOADING",
            meta={"step": "downloading"}
        )
        
        video = temp_dir / Path(file_name).name
        download_from_r2(file_name, str(video))
        
        output_dir = temp_dir / "processed" / video.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        
        dash_dir = output_dir / "dash"
        dash_dir.mkdir(parents=True, exist_ok=True)
        
        self.update_state(
            state="PROBING",
            meta={"step": "ffprobe"}
        )
        
        # ffprobe
        probe_result = probe_video(str(video))
        
        self.update_state(
            state="TRANSCODING",
            meta={"step": "ffmpeg"}
        )
        
        transcode_video(video, probe_result, output_dir, dash_dir)
        
        # Celery task state: Upload processed files
        self.update_state(
            state="UPLOADING",
            meta={"step": "uploading"}
        )

        upload_errors = upload_output_directory_to_r2_bucket(
            local_dir=output_dir,
            video_file_name=video.stem,
        )
        
        if upload_errors:
            logger.error("Errors occurred during upload: %s", upload_errors)
            raise RuntimeError(
                f"{len(upload_errors)} files failed to upload"
            )
        
        # Cleanup not required here
        
        self.update_state(
            state="SUCCESS",
            meta={"step": "completed"}
        )
        