from scenedetect import detect, ContentDetector, open_video
from ..SubtitleGenerator.Timestamps import Timestamp, TimeStamps
from ..Logging.Logger import Logger 
from scenedetect import VideoManager, SceneManager
from ..Caching.Cache import GhostCache

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
    scene_list = detect(fname, ContentDetector(threshold=threshold,min_scene_len=10,
                                               frame_window=3,
                                                min_content_val=10),show_progress=True)
    # scene_list = scene_manager.detect_scenes(video, show_progress=True)
    stamps = []
    for (start,end) in scene_list:
        stamps.append((start.get_seconds(), end.get_seconds()))
    # Logger.log("Finished Detecting Scenes")
    stamps = TimeStamps.from_nums(stamps)
    stamps.sort()
    cache.set_item('scenes', scenes, "basic")
    return stamps