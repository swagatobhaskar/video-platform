from pathlib import Path

class VideoTranscoder:

    def __init__(self):
        pass

    def probe(self, video_path: Path) -> dict:
        return probe_video(str(video_path))

    def transcode(self, video_path: Path, probe_result: dict, output_dir: Path) -> dict:
        pass