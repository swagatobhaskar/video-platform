import logging
import subprocess
from pathlib import Path

from .transcoder import VideoTranscoder
from app.tasks.transcode.utils import (
    generate_renditions, create_output_directories,
    build_ffmpeg_command, probe_video
)

logger = logging.getLogger(__name__)


class FFmpegVideoTranscoder(VideoTranscoder):

    def probe(self, video_path: Path) -> dict:
        return probe_video(str(video_path))

    def transcode(self, video_path: Path, probe_result: dict, output_dir: Path) -> dict:
        renditions = generate_renditions(probe_result["height"])

        if not renditions:
            raise ValueError(f"No valid renditions for source height- {probe_result['height']}")

        create_output_directories(output_dir)

        dash_dir = output_dir / "dash"
    
        cmd = build_ffmpeg_command(
            input_file=str(video_path),
            output_dir=dash_dir,
            renditions=renditions,
            fps=probe_result["fps"]
        )

        logger.info("Starting FFmpeg for %s", video_path)

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.stdout:
            logger.info("FFmpeg stdout:\n%s", result.stdout)

        if result.stderr:
            logger.info("FFmpeg stderr:\n%s", result.stderr)

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed with exit code {result.returncode}: {result.stderr}")

        return {
            "status": "completed",
            "manifest": str(dash_dir / "manifest.mpd"),
            "hls_master": str(dash_dir / "master.m3u8"),
            "metadata": probe_result,
        }
    