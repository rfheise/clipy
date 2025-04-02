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
                                            #    frame_window=3,
                                                # min_content_val=10
                                                ),show_progress=True)
    # scene_list = scene_manager.detect_scenes(video, show_progress=True)
    scenes = [Scene.init_from_pyscene(scene) for scene in scene_list]
    scenes.sort(key=lambda x:x.start)
    cache.set_item('scenes', scenes, "basic")
    return scenes


class Scene():

    def __init__(self, start,end, frame_start, frame_end):
        self.start = start 
        self.end = end 
        self.frame_start = frame_start 
        self.frame_end = frame_end

    @classmethod
    def init_from_pyscene(cls, scene):
        return cls(scene[0].get_seconds(), scene[1].get_seconds(),
                   scene[0].get_frames(), scene[1].get_frames())

    def get_timestamp(self):
        return Timestamp(self.start, self.end)