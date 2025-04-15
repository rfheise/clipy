from ..Config.Config import Config
import subprocess
import os 
from ..Logging.Logger import Logger
from ..Profiler.Profiler import Profiler

#this file just preprocesses the input video file with ffmpeg 
#it preprocesses it to the 25fps 16000HZ that talknet requires

def preprocess_video(video_file):
    out_file = os.path.splitext(os.path.basename(video_file))[0] + "_preprocessed.mp4"
    if os.path.exists(out_file):
        return out_file
    if not Config.debug_mode:
        command = [
            'ffmpeg',
            '-y',                  # Overwrite output file if it exists.
            '-i', video_file,      # Input video file.
            '-stats',
            '-loglevel', 'error',
            '-hide_banner',
            '-r', '25',            # Set output frame rate to 25 fps.
            # '-vf', 'scale=-2:480',
            '-c:v', 'libx264',     # Use libx264 for video encoding.
            '-crf', '18',          # CRF value for quality control.
            '-preset', 'medium',   # Encoding preset.
            '-c:a', 'aac',         # Use AAC for audio encoding.
            '-ar', '48000',        # Set audio sample rate to 48000 Hz.
            '-b:a', '192k',        # Set audio bitrate to 192 kbps.
            out_file         # Output file path.
        ]
    else:
        command = [
            'ffmpeg',
            '-y',                  # Overwrite output file if it exists.
            '-stats',
            '-loglevel', 'error',
            '-hide_banner',
            '-i', video_file,      # Input video file.
            '-r', '25',            # Set output frame rate to 25 fps.
            '-vf', 'scale=-2:480',
            '-c:v', 'libx264',     # Use libx264 for video encoding.
            '-crf', '30',          # CRF value for quality control.
            '-preset', 'fast',   # Encoding preset.
            '-ar', '16000',        # Set audio sample rate to 16000Hz.
            '-b:a', '32k',         # Set audio bitrate to 48 kbps.
            out_file            #  Output file path.
        ]

    Logger.log("Re-Render Video To Be 25fps and 16000Hz")
    Logger.log("Removing this step is in the TODO list since it takes a long time")
    # Execute the command using subprocess
    Profiler.start("Preprocessing Video")
    subprocess.run(command)
    Profiler.stop("Preprocessing Video")
    
    return out_file
    
    