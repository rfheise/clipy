
from .Frame import Frame 
import moviepy.editor as mp

"""
Should be called ObjectTrack but didn't want to go back and update it everywhere.
This module is an abstract class for an object track. 
It is used to represent a track of objects in a video.
Keeps track of the meta data for frames containing the object
See Clip.py for more information on data hierarchy
"""

class Track():


    def __init__(self, scene):
        # scene containing object
        # data should load top down and track shouldn't link back to scene
        # but it is easier to do so for now
        self.scene = scene
        self.frames = []

        # center stores information about how to crop the track
        # right now its just a single (x,y) point but should be 
        # (x,y, timestamp) to keep track of duration of object in scene 
        # this will allow for more complex cropping functionality 
        self._center = None

    def add(self, frame):
        
        #adds frame to list of frames
        self.frames.append(frame)

    @classmethod
    def init_from_raw_frames(cls, scene, frames):

        # initializes a track from a list of raw frames 

        track = cls(scene)
        for i, frame in enumerate(frames):
            track.add(Frame.init_from_cv2_frame(frame, scene.frame_start + i))
        return track 

    def __len__(self):
        return len(self.frames)
    
    def load_frames(self, mode="model"):

        # loads all frames in track
        # loads all frames from scene and iterates over them
        #scenes are small so this inefficiency is fine for now 
        for face in self.frames:
            for i, frame in enumerate(self.scene.get_frames(mode = mode)):
                if face.idx == i + self.scene.frame_start:
                    face.set_cv2(frame)
    
    def free_frames(self):

        # frees frames from memory
        self.scene.free_frames()
        for face in self.frames:
            face.clear_cv2()
    
    def get_center_of_frames(self):

        # gets center of frame
        # each frame object can set it's own center for cropping purposes
        return self.frames[0].center
    
    def get_center_from_none(self):
        
        # to be overwritten by inherited classes
        # initializes center track center if center is none 
        # this center is used for cropping functionality 
        return self.get_center_of_frames()

    def get_center(self):

        # initalizes center if it is none
        if self._center is None:
            self._center =  self.get_center_from_none()
        return self._center