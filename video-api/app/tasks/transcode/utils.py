import json
import subprocess
from pathlib import Path
from fractions import Fraction


TARGET_HEIGHTS = [
    720,
    480,
    360,
]


BITRATE_LADDER = {
    720: {
        # Visual quality target
        "crf": 23,
        # Nominal bitrate for DASH metadata
        "bitrate": "1800k",
        # Peak bitrate ceiling
        "maxrate": "2200k",
        # VBV buffer
        "bufsize": "4400k",
        # H264 profile
        "profile": "high",
    },

    480: {
        "crf": 25,
        "bitrate": "1000k",
        "maxrate": "1200k",
        "bufsize": "2400k",
        "profile": "main",
    },

    360: {
        "crf": 27,
        "bitrate": "600k",
        "maxrate": "700k",
        "bufsize": "1400k",
        "profile": "main",
    },
}


def probe_video(input_path: str):

    cmd = [
        "ffprobe",

        # Hide noisy logs
        "-v", "quiet",

        # Output JSON
        "-print_format", "json",

        # Show stream metadata
        "-show_streams",

        str(input_path)
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True
    )

    data = json.loads(result.stdout)

    # Find first video stream
    video_stream = next(
        s for s in data["streams"]
        if s["codec_type"] == "video"
    )

    return {
        "width": video_stream["width"],
        "height": video_stream["height"],
        "codec": video_stream["codec_name"],
        "fps": float(Fraction(video_stream["r_frame_rate"]))
    }



def generate_renditions(source_height: int):

    renditions = []

    for height in TARGET_HEIGHTS:

        if source_height >= height:

            renditions.append({
                "height": height
            })

    return renditions


def create_output_directories(OUTPUT_ROOT):

    (OUTPUT_ROOT / "dash").mkdir(
        parents=True,
        exist_ok=True
    )


def build_filter_complex(renditions):

    split_count = len(renditions)

    split_outputs = "".join(
        [f"[v{i}]" for i in range(split_count)]
    )

    filter_parts = []

    # Split video stream
    filter_parts.append(
        f"[0:v]split={split_count}{split_outputs}"
    )

    # Scale each stream
    for i, rendition in enumerate(renditions):

        height = rendition["height"]

        filter_parts.append(
            f"[v{i}]"
            f"scale=w=-2:h={height}:flags=lanczos,"
            f"setsar=1,"
            # Force identical display aspect ratio
            f"setdar=16/9"
            f"[v{i}out]"
        )

    return ";".join(filter_parts)



def build_ffmpeg_command(
    input_file,
    output_dir,
    renditions,
    fps
):

    SEGMENT_DURATION = 6

    GOP = int(fps * SEGMENT_DURATION)

    cmd = [

        "ffmpeg", "-y", # Overwrite existing files

        # Cleaner logs
        "-hide_banner",

        # Log level
        "-loglevel", "info",

        # Use all CPU threads
        "-threads", "0",

        "-i", str(input_file),

        "-filter_complex",
        build_filter_complex(renditions),
    ]

    for i, rendition in enumerate(renditions):

        height = rendition["height"]

        settings = BITRATE_LADDER[height]

        cmd += [
            "-map", f"[v{i}out]",
        ]

        cmd += [

            # H.264 encoder
            f"-c:v:{i}", "libx264",

            # Compression efficiency
            f"-preset:v:{i}", "slow",

            # Cartoon optimization
            f"-tune:v:{i}", "animation",

            # Streaming-safe pixel format
            f"-pix_fmt:v:{i}", "yuv420p",

            # H.264 profile
            f"-profile:v:{i}",
            settings["profile"],

            # H.264 level
            f"-level:v:{i}", "4.1",

            # Quality target
            f"-crf:v:{i}",
            str(settings["crf"]),

            # DASH manifest bandwidth metadata
            f"-b:v:{i}", settings["bitrate"],

            # Streaming bitrate ceiling
            f"-maxrate:v:{i}",
            settings["maxrate"],

            # VBV buffer
            f"-bufsize:v:{i}",
            settings["bufsize"],

            # GOP size
            f"-g:v:{i}",
            str(GOP),

            # Minimum GOP size
            f"-keyint_min:v:{i}",
            str(GOP),

            # Disable random scene-cut keyframes
            f"-sc_threshold:v:{i}",
            "0",

            # Force exact segment-aligned keyframes
            f"-force_key_frames:v:{i}",
            f"expr:gte(t,n_forced*{SEGMENT_DURATION})",

            # Deterministic bitrate behavior
            f"-x264-params:v:{i}",
            "nal-hrd=vbr:force-cfr=1",

            # B-frames
            f"-bf:v:{i}",
            "2",
        ]

    cmd += [

        # Map first audio stream
        "-map", "0:a:0?",

        # AAC audio
        "-c:a:0", "aac",

        # Audio bitrate
        "-b:a:0", "96k",

        # Sample rate
        "-ar:a:0", "48000",

        # Stereo
        "-ac:a:0", "2",
    ]

    cmd += [
        "-movflags",
        "+frag_keyframe+empty_moov+default_base_moof",

        # DASH muxer
        "-f", "dash",

        # Segment duration
        "-seg_duration",
        str(SEGMENT_DURATION),

        # Use template naming
        "-use_template", "1",

        # Use timeline
        "-use_timeline", "1",

        "-hls_playlist", "1",

        "-hls_master_name",
        "master.m3u8",

        # Init segments
        "-init_seg_name",
        "init_$RepresentationID$.mp4",

        # Media fragments
        "-media_seg_name",
        "chunk_$RepresentationID$_$Number%05d$.m4s",

        "-adaptation_sets",
        "id=0,streams=0,1,2 id=1,streams=3",

        str(output_dir / "manifest.mpd")
    ]

    return cmd

"""
if __name__ == "__main__":
    INPUT_VIDEO = "/app/input/AP photographers.mp4"
    VIDEO_NAME = Path(INPUT_VIDEO).stem
    OUTPUT_ROOT = Path("/app/output") / VIDEO_NAME
    OUTPUT_ROOT.mkdir( parents=True, exist_ok=True )
    
    print("\nRunning ffprobe...\n")

    # Probe metadata
    probe = probe_video(INPUT_VIDEO)

    print(probe)

    # Generate valid renditions
    renditions = generate_renditions(
        probe["height"]
    )

    # Create directories
    create_output_directories(
        renditions,
        OUTPUT_ROOT
    )

    # Build FFmpeg command
    cmd = build_ffmpeg_command(
        input_file=INPUT_VIDEO,
        output_dir=OUTPUT_ROOT,
        renditions=renditions,
        fps=probe["fps"]
    )

    print("\nGenerated FFmpeg command:\n")

    print(" ".join(cmd))

    print("\nStarting transcoding...\n")

    # Execute FFmpeg
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    print(result.stdout)

    print(result.stderr)

    # Raise exception if FFmpeg failed
    result.check_returncode()

    print("\nTranscoding completed successfully!\n")
"""