from ..Track import Track 
from ..Frame import Frame 
from ...Utilities import Logger

class Face(Frame):
    
    def __init__(self, idx, center, width, height):
        super().__init__(idx, center, width, height)
        self.bbox = None 
        self.conf = None
    
    def set_face_detection_args(self, bbox, conf):

        self.bbox = bbox 
        self.conf = conf

    @classmethod
    def init_from_frame(cls, frame):
        face = cls(frame.idx, frame.center, frame.width, frame.height)



class FacialTrack(Track):
   
    def __init__(self, scene):
        
        super().__init__(scene)
        self.score = None 

    def set_score(self, score):
        self.score = score


    def add(self, face):

        if type(face) is not Face:
            Logger.log_warning("non-face Frame added to FacialTrack")
        
        super().add(face)