from .transcoder import VideoTranscoder

class FFmpegVideoTranscoder(VideoTranscoder):

    def probe(self, video_path):
        return super().probe(video_path)

    def transcode(self, video_path, probe_result, output_dir):
        return super().transcode(video_path, probe_result, output_dir)
    
