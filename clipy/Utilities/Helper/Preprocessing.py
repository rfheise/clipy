from ..Config.Config import Config
import subprocess
import os 
from ..Logging.Logger import Logger
from ..Profiler.Profiler import Profiler

#this file just preprocesses the input video file with ffmpeg 
#it preprocesses it to the 25fps 16000HZ that talknet requires
    
def to_ffmpeg_time(seconds):
    hours = int(seconds/3600)
    minutes = int((seconds % 3600)/60)
    scnds = int(seconds % 60)
    milliseconds = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02}:{minutes:02}:{scnds:02}.{milliseconds:03}"

#gets actual display h,w of input video and padding
def get_display_crop(video_path):
    """
    Uses ffprobe to get display vs. coded dimensions, then
    computes how many pixels to chop off on the left/top.
    Returns (w, h, pad_x, pad_y).
    """
    # ask ffprobe for width,height,coded_width,coded_height
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,coded_width,coded_height',
        '-of', 'csv=p=0',
        video_path
    ]
    out = subprocess.check_output(cmd).decode().strip().split(",")
    # Expect four lines: width, height, coded_width, coded_height
    disp_w, disp_h, coded_w, coded_h = map(int, out)
    pad_w = coded_w - disp_w
    pad_h = coded_h - disp_h
    # usually split evenly
    pad_x = pad_w
    pad_y = pad_h 
    return disp_w, disp_h, pad_x, pad_y

def preprocess_video(video_file, out_file, start, end):
    
    start = to_ffmpeg_time(start)
    end = to_ffmpeg_time(end)
    
    command = [
        'ffmpeg',
        '-y',                  # Overwrite output file if it exists.
        '-stats',
        '-loglevel', 'error',
        '-hide_banner',
        '-ss', start,
        '-to', end, 
        '-i', video_file,      # Input video file.
        '-r', '25',            # Set output frame rate to 25 fps.
        '-vf', 'scale=-2:480',
        '-c:v', 'libx264',     # Use libx264 for video encoding.
        '-crf', '35',          # CRF value for quality control.
        '-preset', 'ultrafast',   # Encoding preset.
        '-ar', '16000',        # Set audio sample rate to 16000Hz.
        '-b:a', '32k',         # Set audio bitrate to 48 kbps.
        out_file            #  Output file path.
    ]

    # Execute the command using subprocess
    Profiler.start("Preprocessing Video")
    # print(" ".join(command))
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    Profiler.stop("Preprocessing Video")
    
    return out_file
    



