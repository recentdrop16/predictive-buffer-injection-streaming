import os
import subprocess

VIDEOS_DIR = "videos"
SEGMENTS_DIR = "segments"
SEGMENT_TIME = 1

videos = ["video1.mp4", "video2.mp4", "video3.mp4"]

# 🔥 your exact ffmpeg path
FFMPEG_PATH = r"C:\Users\Anthony\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"

os.makedirs(SEGMENTS_DIR, exist_ok=True)

for video_file in videos:
    input_path = os.path.join(VIDEOS_DIR, video_file)
    video_name = os.path.splitext(video_file)[0]
    output_dir = os.path.join(SEGMENTS_DIR, video_name)
    os.makedirs(output_dir, exist_ok=True)

    output_pattern = os.path.join(output_dir, "seg_%03d.mp4")

    cmd = [
        FFMPEG_PATH,   # 🔥 FIXED HERE
        "-i", input_path,
        "-c", "copy",
        "-map", "0",
        "-f", "segment",
        "-segment_time", str(SEGMENT_TIME),
        "-reset_timestamps", "1",
        output_pattern
    ]

    print(f"Splitting {video_file}...")
    subprocess.run(cmd, check=True)

print("Done.")