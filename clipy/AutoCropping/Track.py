
from .Frame import Frame 

class Track():


    def __init__(self, scene):
        self.scene = scene
        self.frames = []

    def add(self, frame):

        self.frames.append(frame)
    
    def crop(self):
        # TODO
        # implement crop for custom tracks
        # if crop not set don't do anything just add the whole
        # thing resized the video 
        pass 

    @classmethod
    def init_from_raw_frames(cls, scene, frames):
        track = cls(scene)
        for i, frame in enumerate(frames):
            track.add(Frame.init_from_cv2_frame(frame, scene.frame_start + i))
    
    def __len__(self):
        return len(self.frames)