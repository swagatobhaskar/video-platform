from abc import ABC, abstractmethod
from pathlib import Path

# make the base class an interface/abstract class.
class VideoTranscoder(ABC):

    @abstractmethod
    def probe(self, video_path: Path) -> dict:
        pass

    @abstractmethod
    def transcode(self, video_path: Path, probe_result: dict, output_dir: Path) -> dict:
        pass
    