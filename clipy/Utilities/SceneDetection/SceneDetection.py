from scenedetect import detect, ContentDetector, open_video, AdaptiveDetector
from ..SubtitleGenerator.Timestamps import Timestamp, TimeStamps
from ..Logging.Logger import Logger 
from scenedetect import VideoManager, SceneManager, open_video
from ..Caching.Cache import GhostCache
from ..Profiler.Profiler import Profiler
from ..Helper.Preprocessing import get_display_crop
import subprocess
import moviepy.editor as mp
import os 


#This function just uses the scene detect library in order to 
#identify cuts in the video file
def process_input_video(video_file, outfile, out_res=360):
    
    command = [
        'ffmpeg',
        '-y',                  # Overwrite output file if it exists.
        '-stats',
        '-loglevel', 'error',
        '-hide_banner',
        '-i', video_file,      # Input video file.
        '-vf', f'scale=-2:{out_res}',
        '-c:v', 'libx264',     # Use libx264 for video encoding.
        '-crf', '35',          # CRF value for quality control.
        '-preset', 'ultrafast',   # Encoding preset.
        '-ar', '16000',        # Set audio sample rate to 16000Hz.
        '-b:a', '32k',         # Set audio bitrate to 48 kbps.
        outfile            #  Output file path.
    ]

    Logger.log("Re-rendering input for faster scene detection")
    subprocess.run(command)

    return outfile

    


def detect_scenes(fname, threshold=10, cache=GhostCache):

    if cache.exists("scenes"):
        scenes = cache.get_item("scenes")
        return scenes
    
    Logger.log("Detecting Scenes")

    Profiler.start("Scene Detection")

    output_res = 360
    tmp_file = "tmp_file.mp4"
    video_resolution = get_display_crop(fname)[1] #gets video display height

    #if more than twice the size of input res 
    #use ffmpeg to re-render the video for faster scene detection
    if video_resolution/2 >= output_res:
        fname = process_input_video(fname, tmp_file, output_res)
    

    video = open_video(fname)
    scene_manager = SceneManager()
    scene_manager.add_detector(AdaptiveDetector(
            adaptive_threshold=3.0,
            min_scene_len=10,
            window_width=3,
            min_content_val=10
        ))

    # Set downscale factor to 2 (half resolution). If auto_downscale is enabled,
    # this parameter might be ignored, so you may want to disable it:
    scene_manager.auto_downscale = True
    # scene_manager.downscale = 4

    scene_manager.detect_scenes(video, show_progress=True)
    scenes = scene_manager.get_scene_list()
    #calls scene detect library function to idenfity cuts
    # scenes = detect(
    #     fname,
    #     AdaptiveDetector(
    #         adaptive_threshold=3.0,
    #         min_scene_len=10,
    #         window_width=3,
    #         min_content_val=10
    #     ),
    #     show_progress=True
    # )

    #sorts scenes by start time
    scenes.sort(key=lambda x:x[0].get_seconds())

    Profiler.stop("Scene Detection")
    cache.set_item('scenes', scenes, "basic")

    if fname == tmp_file:
        os.remove(tmp_file)
    return scenes


