from ..Utilities import detect_scenes, GhostCache, Logger, Timestamp
from .Scene import Scene
import math
import cv2 
import numpy as np
import moviepy.editor as mp 

class Clip():
    counter = 0
    def __init__(self, video_file, scenes, cache=GhostCache()):
        self.cache = cache
        self.scenes = scenes
        self.video_file = video_file
        self.options = {}
        self.id = Clip.counter
        self.pizzazz = []
        self.aspect_ratio = 9/16
        Clip.counter += 1
        self.width = None
        self.height = None

    def set_dims(self,frame):
        self.width = round(frame.shape[0] * self.aspect_ratio)
        self.height = frame.shape[0]

    def get_audio(self):
        video = mp.VideoFileClip(self.video_file)
        audio = video.audio.subclip(self.scenes[0].start, self.scenes[-1].end)
        return audio 
    
    def render(self):
        
        frames = []
        for scene in self.scenes:
            scene.load_frames(mode="render")
            center = scene.get_center()
            keep_ratio = (center == scene.scene_center)
            for frame in scene.get_frames():
                if self.height is None or self.width is None:
                    self.set_dims(frame)
                # print(center)
                new_frame =  self.crop_cv2(frame, center, keep_ratio)
                frames.append(new_frame)     
                
        return frames, self.get_audio() 
    
    def get_dims_from_center(self, c, width, max_val):

        xs = int(c - math.floor(width/2))
        xe = int(c + math.ceil(width/2))
        if xe >= max_val:
            return (max_val - width, max_val)
        if xs <= 0:
            return (0, width)
        return (xs, xe)
    
    def crop_cv2(self, frame, center, keep_ratio):

        
        if not keep_ratio:
            return self.actually_crop(frame, center)
        else:
            return self.resize_for_frame(frame)
    
    def actually_crop(self, frame, center):

        xs, xe = self.get_dims_from_center(center[0], self.width, frame.shape[1])
        #keep height the same
        # ys, ye = (0, self.height)
        # print("crop", xs, xe, 0, self.height)
        return frame[:, xs:xe]

    def resize_for_frame(self, frame):

        new_w = self.width 
        new_h = int(self.width * (frame.shape[0]/frame.shape[1]))
        frame = cv2.resize(frame, (int(new_w), int(new_h)))
        #make it work for b&w video
        if len(frame.shape) == 3:
            new_f = np.zeros((self.height, self.width, 3))
        else:
            new_f = np.zeros((self.height, self.width))
        ys = int(new_f.shape[0]/2) - math.floor(frame.shape[0]/2)
        ye = ys + frame.shape[0]
        new_f[ys:ye] = frame 
        return new_f.astype(np.uint8)



    
    @classmethod
    def init_from_timestamp(cls, video_file, timestamp, cache=GhostCache()):
        #init clip with scenes
        scenes = detect_scenes(video_file, cache=cache)
        # get all scenes in interval
        clip_scenes = []
        for scene in scenes:
            scene = Scene.init_from_pyscene(video_file, scene)
            # double check this if statement
            # seems kind of sus ngl
            if (scene.start >= timestamp.start and scene.start < timestamp.end) or \
                (scene.end <= timestamp.end and scene.start >= timestamp.start) or \
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

    def add_pizzazz(self, pizzazz):
        self.pizzazz.append(pizzazz)
    
    def free_frames(self):

        for scene in self.scenes:
            scene.free_frames_from_tracks()
    
    def get_total_frames(self):
        #should be implemented in clip object

        total_frames = 0
        for scene in self.scenes:
            # end frame is not inclusive
            total_frames += scene.frame_end - scene.frame_start
        return total_frames