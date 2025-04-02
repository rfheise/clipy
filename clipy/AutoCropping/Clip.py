from .Frame import FrameStamp
from ..Utilities import detect_scenes, GhostCache, Logger

class Clip():

    def __init__(self, video_file, frame_stamp):

        self.tracks = None 
        self.frame_stamp = frame_stamp
        self.scenes = None 
        self.video_file = video_file
    
    def set_tracks(self, tracks):
        self.tracks = tracks

    def render(self, fname):

        #TODO
        # render clip and store it at fname 

        pass 
    
    def get_scenes(self):
        return self.scenes
    
    @classmethod
    def initialize_clip(cls, video_file, timestamp, cache=GhostCache):
        
        #init clip with scenes
        clip = cls(video_file, timestamp)
        scenes = detect_scenes(video_file, cache=cache)
        # get all scenes in interval
        clip.scenes = []
        for scene in scenes:
            if scene.start <= timestamp.start and scene.end >= timestamp.start:
                clip.scenes.append(scene)
        
        # shortend start and end scene
        clip.scenes[0].trim_scene(timestamp)
        clip.scenes[-1].trim_scene(timestamp)
        clip.scenes = clip.scenes

        return clip

    def load_scenes(self):
        #TODO
        #load scenes for clip 
        #create scene object for better control
        pass