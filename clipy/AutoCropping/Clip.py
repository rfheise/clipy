from ..Utilities import detect_scenes, GhostCache, Logger, Timestamp
from .Scene import Scene

class Clip():
    counter = 0
    def __init__(self, video_file, scenes, cache=GhostCache()):
        self.cache = cache
        self.scenes = scenes
        self.video_file = video_file
        self.options = {}
        self.id = Clip.counter 
        Clip.counter += 1

    def render(self, fname):

        #TODO
        # render clip and store it at fname 

        pass 
    
    @classmethod
    def init_from_timestamp(cls, video_file, timestamp, cache=GhostCache()):
        #init clip with scenes
        scenes = detect_scenes(video_file, cache=cache)
        # get all scenes in interval
        clip_scenes = []
        for scene in scenes:
            scene = Scene.init_from_pyscene(video_file, scene)
            if (scene.start >= timestamp.start and scene.start < timestamp.end) or \
                (scene.end <= timestamp.end and scene.start > timestamp.start) or \
                (scene.start < timestamp.start and scene.end > timestamp.end):
                clip_scenes.append(scene)

        # shortend start and end scene
        clip_scenes[0].trim_scene(timestamp)
        clip_scenes[-1].trim_scene(timestamp)
        return cls(video_file, clip_scenes, cache)
    
    def get_scenes(self):
        return self.scenes
    
    def get_start(self):
        return self.scenes[0].start
    
    def get_end(self):
        return self.scenes[-1].end
    
    def get_duration(self):
        return self.scenes[-1].end - self.scenes[0].start
    
    def get_start_frame(self): 
        return self.scenes[0].frame_start
    
    def get_end_frame(self):
        return self.scenes[-1].frame_end
    
    def get_timestamp(self):
        return Timestamp(self.scenes[0].start, self.scenes[-1].end)
    
    def crop(self, aspect_ratio=(9/16)):

        # all crop does is set centers all the way down
        self.options["aspect_ratio"] = aspect_ratio
        for scene in self.scenes:
            scene.set_centers()
    
    def set_scenes(self, scenes):
        self.scenes = scenes
    
