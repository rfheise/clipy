from ..Utilities import Timestamp 

"""
Should be called ObjectFrame but didn't want to go back and update it everywhere. 
This module represents a default object frame.
It stores the metadata of an object in a frame in a video track. 
See Clip.py for more information on data hierarchy.
"""
class Frame():


    def __init__(self, idx, center, width, height, raw_frame=None):

        self.idx = idx
        self.center = center 
        self.width = width 
        self.height = height
        self.raw_frame = raw_frame

    @classmethod
    def init_from_raw_frame(cls, frame, frame_idx):
        # initializes a frame from a raw cv2 frame
        # frame idx is the position of the frame in the full video file
        height, width =  frame.get_cv2().shape[:2]
        center = (width//2, height//2)
        return cls(frame_idx, center, width, height, frame)