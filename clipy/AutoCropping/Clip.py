from ..Utilities import detect_scenes, GhostCache, Logger, Timestamp
from .Scene import Scene
import math
import cv2 
import numpy as np
import moviepy.editor as mp 


"""This module represents a video clip object. It is what gets returned from the AutoCropper.
It stores of the clip metadata and the scenes in the clip. It is used to render the video clip and get the audio for the clip.
It uses this metadata to render the output video clip.

Here is the general hierarchical structure of the clip object:
Clip
    | Data stored for video clip
    |-- Scenes
        | Scene objects that store information about each video "cut"
        |-- Tracks
            | (Object) Track object that stores information about an object in the scene
            |-- Frames
                | (Object) Frame stores information about an object in a particular frame

This hierarchy is important to understand because it is how the clip object is structured.
Its a little scuffed and changed a few times throughout the implementation but I've settled on this structure as it seems logical. 
You can tell how things used to work as some implementations don't make sense and were band-aid solutions to get things working.
Honestly a lot of the functionality in this needs redone so it properly fits with this flow. 

If you plan on adding additional track types please make sure they fit in this hierarchy.
"""

class Clip():

    # counter for clip id
    counter = 0
    def __init__(self, video_file, scenes, cache=GhostCache()):
        
        self.cache = cache

        #Scene[]
        self.scenes = scenes
        #raw input video file
        self.video_file = video_file

        #additional configuration options
        #not really used but might be used later
        self.options = {}

        self.id = Clip.counter

        # output aspect ratio
        self.aspect_ratio = 9/16

        Clip.counter += 1

        #output video width and height
        self.width = None
        self.height = None

    def set_dims(self,frame):
        # sets dimensions of the output video before rendering
        self.width = round(frame.shape[0] * self.aspect_ratio)
        self.height = frame.shape[0]

    def get_audio(self):
        # gets clip audio as movie py audio object
        # easy implementation for initial rendering
        # however a more complex format is probably needed for 
        # additional pizzazz functionality
        # maybe a custom Audio class?
        video = mp.VideoFileClip(self.video_file)
        audio = video.audio.subclip(self.scenes[0].start, self.scenes[-1].end)

        return audio 
    
    def render(self):
        #TODO after looking over this code with non-sleep deprived eyes
        #it's kind of bad and needs redone 
        #should have functionality of multiple "centers"
        #should handle variable aspect ratios not just binary (is 9:16 or nah)

        frames = []
        # renders all "shots in clip"
        for scene in self.scenes:
            
            #loads frames from disk
            scene.load_frames(mode="render")
            center = scene.get_center()
            
            #keeps original aspect ratio and just resizes the frame if 
            #custom center is not detected
            keep_ratio = (center == scene.scene_center)
            
            for frame in scene.get_frames():
                if self.height is None or self.width is None:
                    self.set_dims(frame)

                # crops frame and adds it to list of rendered frames
                new_frame =  self.crop_cv2(frame, center, keep_ratio)
                frames.append(new_frame)     
        
        #returns rendered frames and audio
        # will be combined in Video Processing step
        return frames, self.get_audio() 
    
    def get_dims_from_center(self, c, width, max_val):
        
        #gets center width of clip since the height remains the same
        xs = int(c - math.floor(width/2))
        xe = int(c + math.ceil(width/2))
        if xe >= max_val:
            return (max_val - width, max_val)
        if xs <= 0:
            return (0, width)
        
        # returns start and end of crop
        return (xs, xe)
    
    def crop_cv2(self, frame, center, keep_ratio):

        # if keep ratio of og clip is not the same
        # actually crop it 
        # otherwise resize it
        if not keep_ratio:
            return self.actually_crop(frame, center)
        else:
            return self.resize_for_frame(frame)
    
    def actually_crop(self, frame, center):
        
        #get start and end of crop
        xs, xe = self.get_dims_from_center(center[0], self.width, frame.shape[1])
        
        #keep height the same and return new frame
        return frame[:, xs:xe]

    def resize_for_frame(self, frame):
        """Adds black border to original frame and resizes it 
        to fit inside of the short. If you're confused about what this does
        see a few demo videos and it should become obvious. 

        Args:
            frame (cv2 image): raw old frame

        Returns:
            (cv2 image): rendered new frame
        """
        new_w = self.width 
        new_h = int(self.width * (frame.shape[0]/frame.shape[1]))

        #resizes old frame to be new width and height to fit inside 
        #short video whilst maintaining the same aspect ratio
        frame = cv2.resize(frame, (int(new_w), int(new_h)))
        
        #make it work for b&w video
        #makes the new frame entirely black
        if len(frame.shape) == 3:
            new_f = np.zeros((self.height, self.width, 3))
        else:
            new_f = np.zeros((self.height, self.width))
        
        #adds old frame inside of new frame and returns it

        ys = int(new_f.shape[0]/2) - math.floor(frame.shape[0]/2)
        ye = ys + frame.shape[0]
        new_f[ys:ye] = frame 
        return new_f.astype(np.uint8)



    
    @classmethod
    def init_from_timestamp(cls, video_file, timestamp, cache=GhostCache()):

        #initializes a clip from a video file & (start, end timestamp)
        scenes = detect_scenes(video_file, cache=cache)
        # get all scenes in interval
        clip_scenes = []
        for scene in scenes:
            # intializes scene from pyscene object
            scene = Scene.init_from_pyscene(video_file, scene)

            # double check this if statement
            # seems kind of sus ngl
            # checks to see if scene is in the clip
            if (scene.start >= timestamp.start and scene.start < timestamp.end) or \
                (scene.end <= timestamp.end and scene.start >= timestamp.start) or \
                (scene.start < timestamp.start and scene.end > timestamp.end):
                clip_scenes.append(scene)

        # trim scene to make sure it fits in timestamp
        clip_scenes[0].trim_scene(timestamp)
        clip_scenes[-1].trim_scene(timestamp)

        # return clip
        return cls(video_file, clip_scenes, cache)
    
    def get_scenes(self):
        return self.scenes
    
    def get_start(self):
        #returns start of clip in seconds
        return self.scenes[0].start
    
    def get_end(self):
        #returns end of clip in seconds
        return self.scenes[-1].end
    
    def get_duration(self):
        #gets duration in seconds
        return self.scenes[-1].end - self.scenes[0].start
    
    def get_start_frame(self): 
        #gets start of clip in frames
        return self.scenes[0].frame_start
    
    def get_end_frame(self):
        #gets end of clip in frames
        return self.scenes[-1].frame_end
    
    def get_timestamp(self):

        #returns timestamp of start and end of clip
        #uses start value of first scene and end value of last scene
        return Timestamp(self.scenes[0].start, self.scenes[-1].end)
    
    def crop(self, aspect_ratio=(9/16)):

        # all crop does is set centers all the way down
        # it doesn't actually crop the video
        # that is done in render during the video processing phase
        self.options["aspect_ratio"] = aspect_ratio
        for scene in self.scenes:
            scene.set_centers()

    def set_scenes(self, scenes):

        self.scenes = scenes
    
    def free_frames(self):

        # frees clip frames from memory
        for scene in self.scenes:
            scene.free_frames_from_tracks()
    
    def get_total_frames(self):

        #gets duration of clip in frames
        total_frames = 0
        for scene in self.scenes:
            # end frame is not inclusive
            total_frames += scene.frame_end - scene.frame_start
        return total_frames