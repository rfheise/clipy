
from .Frame import Frame 
import moviepy.editor as mp

class Track():


    def __init__(self, scene):
        self.scene = scene
        self.frames = []
        self._center = None

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
        return track 

    def __len__(self):
        return len(self.frames)
    
    def load_frames(self, mode="model"):
        # self.scene.load_frames(mode = mode)
        #scenes are small so this inefficiency is fine for now 
        for face in self.frames:
            for i, frame in enumerate(self.scene.get_frames(mode = mode)):
                if face.idx == i + self.scene.frame_start:
                    face.set_cv2(frame)
    
    def free_frames(self):
        self.scene.free_frames()
        for face in self.frames:
            face.clear_cv2()
    
    def get_center_of_frames(self):
        return self.frames[0].center
    
    def get_center_from_none(self):
        return self.get_center_of_frames()

    def get_center(self):
        if self._center is None:
            self._center =  self.get_center_from_none()
        return self._center