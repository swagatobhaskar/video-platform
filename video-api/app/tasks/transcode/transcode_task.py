from app.celery_worker import celery
import time
import asyncio
from pathlib import Path
import os
from .utils import probe_video, generate_renditions, create_output_directories, build_ffmpeg_command
import logging 

logger = logging.getLogger(__name__)

@celery.task(
    bind=True,
    # for long tasks
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    )
def transcode_video(self, file_path: str): #file_path will be the video name as kept in R2
    
    import subprocess
        
    # Celery task state
    self.update_state(
        state="PROBING",
        meta={"step": "ffprobe"}
    )
    
    video = Path(file_path)
    
    # Use the stem (filename without extension) as the folder name
    output_dir = video.parent / "processed" / video.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Now you can use output_dir to store DASH/HLS segments
    # Example:
    dash_dir = output_dir / "dash"
    dash_dir.mkdir(parents=True, exist_ok=True)
    
    # output_file = output_dir / f"{video.stem}.mp4"
    # manifest_path = output_dir / "dash" / "manifest.mpd"
    
    # ffprobe
    probe_result = probe_video(str(video))
    
    self.update_state(
        state="TRANSCODING",
        meta={"step": "ffmpeg"}
    )
    
    # generate renditions
    renditions = generate_renditions(
        probe_result["height"]
    )
    
    # Create directories
    create_output_directories(
        OUTPUT_ROOT=output_dir
    )

    # Build FFmpeg command
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
    
    # Delete original uploaded file. After result.check_returncode()
    try:
        os.remove(file_path)
        logger.info("Deleted source file: %s", file_path)
    except Exception as e:
        logger.warning("Failed to delete source file: %s", e)
    
    return {
        "status": "completed",
        # "input": str(video),
        # "output": str(manifest_path),
        "manifest": str(dash_dir / "manifest.mpd"), # "uploads/processed/dash/manifest.mpd",
        "hls_master": str(dash_dir / "master.m3u8"), # "uploads/processed/dash/master.m3u8",
        "metadata": probe_result,
    }