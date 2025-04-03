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
    
    def compare(self, other_face, iou_thres=.5):
        return Face.bb_intersection_over_union(self.bbox, other_face.bbox) > iou_thres
    
    @staticmethod
    def bb_intersection_over_union(boxA, boxB):
        # Copied directly from TALKNET REPO
        # https://github.com/TaoRuijie/TalkNet-ASD

        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        iou = interArea / float(boxAArea + boxBArea - interArea)

        return iou



class FacialTrack(Track):
   
    def __init__(self, scene):
        
        super().__init__(scene)
        self.score = None 

    def set_score(self, score):
        self.score = score

    def contains_face(self, face):

        return self.frames[-1].compare(face)

    def add(self, face):

        if type(face) is not Face:
            Logger.log_warning("non-face Frame added to FacialTrack")
        
        super().add(face)
    
    @property
    def last_idx(self):

        if len(self.frames) == 0:
            return -1
        return self.frames[-1].idx