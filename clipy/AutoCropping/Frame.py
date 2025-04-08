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


    def __init__(self, idx, center, width, height, cv2_img=None):

        self.idx = idx
        self.center = center 
        self.width = width 
        self.height = height
        self.cv2_img = cv2_img

    @classmethod
    def init_from_cv2_frame(cls, frame, frame_idx):

        height, width =  frame.shape[:2]
        center = (width//2, height//2)
        return cls(frame_idx, center, width, height)

    def crop_frame(self, crop_algo):

        #TODO
        #crop frame using generic process
        #possibly override for various types of frames
        pass

    def set_cv2(self, cv2_img):

        #load frame and store in cv2
        self.cv2 = cv2_img
    
    def clear_cv2(self):
        self.set_cv2(None)