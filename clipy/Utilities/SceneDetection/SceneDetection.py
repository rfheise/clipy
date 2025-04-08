from scenedetect import detect, ContentDetector, open_video
from ..SubtitleGenerator.Timestamps import Timestamp, TimeStamps
from ..Logging.Logger import Logger 
from scenedetect import VideoManager, SceneManager
from ..Caching.Cache import GhostCache
from ..Profiler.Profiler import Profiler
import cv2
import moviepy.editor as mp

def detect_scenes(fname, threshold=10, cache=GhostCache):
    # video = open_video(fname)
    # scene_manager = SceneManager()
    # scene_manager.add_detector(
    #     ContentDetector(threshold=threshold,min_scene_len=10)
    #     )
    if cache.exists("scenes"):
        scenes = cache.get_item("scenes")
        return scenes
    Logger.log("Detecting Scenes")
    Profiler.start("Scene Detection")
    scenes = detect(fname, ContentDetector(threshold=threshold,min_scene_len=10,
                                            #    frame_window=3,
                                                # min_content_val=10
                                                ),show_progress=True)
    # scene_list = scene_manager.detect_scenes(video, show_progress=True)
    scenes.sort(key=lambda x:x[0].get_seconds())
    Profiler.stop("Scene Detection")
    cache.set_item('scenes', scenes, "basic")
    return scenes


