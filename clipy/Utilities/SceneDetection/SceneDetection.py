from scenedetect import detect, ContentDetector, open_video
from ..SubtitleGenerator.Timestamps import Timestamp, TimeStamps
from ..Logging.Logger import Logger 
from scenedetect import VideoManager, SceneManager
from ..Caching.Cache import GhostCache
import cv2

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
    scenes = [Scene.init_from_pyscene(fname, scene) for scene in scene_list]
    scenes.sort(key=lambda x:x.start)
    cache.set_item('scenes', scenes, "basic")
    return scenes


class Scene():

    def __init__(self, video_file, start,end, frame_start, frame_end):
        self.start = start 
        self.end = end 
        self.frame_start = frame_start 
        self.frame_end = frame_end
        self.video_file = video_file
        self.frames = None

    @classmethod
    def init_from_pyscene(cls, fname, scene):
        return cls(fname, scene[0].get_seconds(), scene[1].get_seconds(),
                   scene[0].get_frames(), scene[1].get_frames())

    def get_timestamp(self):
        return Timestamp(self.start, self.end)
    
    def trim_scene(self, timestamp):
        
        if timestamp.start > self.start:
            self.start  = timestamp.start 
            self.frame_start = Scene.get_frame_at_timestamp(timestamp.start)
        if timestamp.end < self.end:
            self.end = timestamp.end 
            self.frame_end = Scene.get_frame_at_timestamp(timestamp.end)

    def get_frames(self):

        if self.frames is None:
            self.load_frames()
        return self.frames 
    
    def load_frames(self):
        #TODO load frames from video input file
        pass
    
    def free_frames(self):
        self.frames = None

    @staticmethod
    def get_frame_at_timestamp(video_path, timestamp_sec):
        #vibe coded with chatgpt


        # Open the video file.
        cap = cv2.VideoCapture(video_path)

        # Get frames per second (FPS) of the video.
        fps = cap.get(cv2.CAP_PROP_FPS)
        # Calculate the frame number.
        frame_number = int(timestamp_sec * fps)

        return frame_number