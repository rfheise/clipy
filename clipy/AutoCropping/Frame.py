from ..Utilities import Timestamp 

"""
Should be called ObjectFrame but didn't want to go back and update it everywhere. 
This module represents a default object frame.
It stores the metadata of an object in a frame in a video track. 
See Clip.py for more information on data hierarchy.
"""
class Frame():


    def __init__(self, idx, center, width, height, cv2_img=None):

        self.idx = idx
        self.center = center 
        self.width = width 
        self.height = height
        self.cv2_img = cv2_img

    @classmethod
    def init_from_cv2_frame(cls, frame, frame_idx):
        # initializes a frame from a raw cv2 frame
        # frame idx is the position of the frame in the full video file
        height, width =  frame.shape[:2]
        center = (width//2, height//2)
        return cls(frame_idx, center, width, height)

    def set_cv2(self, cv2_img):

        #load frame and store in cv2
        self.cv2 = cv2_img
    
    def clear_cv2(self):

        #removes cv2 image from memory
        self.set_cv2(None)