from scenedetect import detect, ContentDetector, open_video, AdaptiveDetector
from ..SubtitleGenerator.Timestamps import Timestamp, TimeStamps
from ..Logging.Logger import Logger 
from scenedetect import VideoManager, SceneManager
from ..Caching.Cache import GhostCache
from ..Profiler.Profiler import Profiler
import cv2
import moviepy.editor as mp

#This function just uses the scene detect library in order to 
#identify cuts in the video file

def detect_scenes(fname, threshold=10, cache=GhostCache):

    if cache.exists("scenes"):
        scenes = cache.get_item("scenes")
        return scenes
    
    Logger.log("Detecting Scenes")

    Profiler.start("Scene Detection")

    #calls scene detect library function to idenfity cuts
    scenes = detect(
        fname,
        AdaptiveDetector(
            adaptive_threshold=3.0,
            min_scene_len=10,
            window_width=3,
            min_content_val=10
        ),
        show_progress=True
    )

    #sorts scenes by start time
    scenes.sort(key=lambda x:x[0].get_seconds())

    Profiler.stop("Scene Detection")
    cache.set_item('scenes', scenes, "basic")
    return scenes


