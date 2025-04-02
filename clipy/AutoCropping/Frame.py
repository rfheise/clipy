from ..Utilities import Timestamp 


class Framestamp(Timestamp):

    def __init__(self, start, end, fps):

        super().__init__(start, end)
        self.start_frame = Framestamp.frame_from_fps(start, fps)
        self.end_frame = Framestamp.frame_from_fps(end, fps)
    
    @staticmethod
    def frame_from_fps(t, fps):
        #TODO convert time in seconds to frame index
        pass

class Frame():


    def __init__(self, idx, center, width, height):

        self.idx = idx
        self.center = center 
        self.width = width 
        self.height = height

    @classmethod
    def init_from_cv2_frame(cls, frame):
        #TODO
        #initialize frame object form cv2 frame 
        pass 

    def crop_frame(self, crop_algo):

        #TODO
        #crop frame using generic process
        #possibly override for various types of frames
        pass
