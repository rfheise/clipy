from ..Track import Track 
from ..Frame import Frame 
from ...Utilities import Logger, Helper, Timestamp, TimeStamps
import cv2 
import moviepy.editor as mp
import os
from scipy.interpolate import interp1d
import numpy as np 

"""
This file is used to implement the facial track and face objects. 
These are used to store metadata about facial tracks and face objects during the autocropping phase. 
See Clip.py, Frame.py, and Track.py for more information
"""

class Face(Frame):
    
    def __init__(self, idx, center, width, height):
        super().__init__(idx, center, width, height)
        self.bbox = None 
        self.conf = None
        self.score = None
    
    def set_score(self, score):
        
        #sets asd (active speaker detection) score of face
        self.score = score
    
    def get_score(self):
        
        #gets asd score of face
        if self.score is None:
            Logger.log_error("score not processed")
            exit(3)
        return self.score
    
    def crop_cv2(self):

        #crops face in frame using bounding box

        if self.cv2 is None:
            Logger.log_error("cv2 not loaded")
            exit(2)
        bbox = [int(i) for i in self.bbox]
        #resizes bounding box to be within frame
        x1 = max(bbox[0], 0)
        x2 = min(bbox[2], self.cv2.shape[1])
        y1 = max(bbox[1],0)
        y2 = min(bbox[3], self.cv2.shape[0])
        self.cv2 = self.cv2[y1:y2, x1:x2]

        return self.cv2 
    
    def set_face_detection_args(self, bbox, conf):

        #sets face detection metadata
        self.set_bbox(bbox)
        self.conf = conf

    def crop_bbox(self, bbox):
        #crops bbox so it's within frame bounds
        bbox[0] = max(bbox[0],0)
        bbox[1] = max(bbox[1],0)
        bbox[2] = min(bbox[2], self.width)
        bbox[3] = min(bbox[3], self.height)
        return bbox
    
    def set_bbox(self, bbox):

        #makes sure bbox within frame
        bbox = self.crop_bbox(bbox)

        #makes sure bbox has non-zero area
        if int(bbox[0]) == int(bbox[2]):
            bbox[0] -= 1
            bbox[2] += 1
        if int(bbox[1]) == int(bbox[3]):
            bbox[1] -= 1
            bbox[3] += 1
        
        #makes bbox within frame in case dims changed after update
        bbox = self.crop_bbox(bbox)


        self.bbox = bbox 

        #sets center to be center of face and not video
        self.center = self.get_center_from_bbox()

    def get_center_from_bbox(self):

        x = int((self.bbox[2] + self.bbox[0])/2)
        y = int((self.bbox[3] + self.bbox[1])/2)
        return (x,y)
    
    @classmethod
    def init_from_frame(cls, frame):

        # inits face from frame object
        face = cls(frame.idx, frame.center, frame.width, frame.height)
        return face
    
    def compare(self, other_face, iou_thres=.5):
        
        #compares faces to see if they are the same
        #doesn't actually compare the faces but rather facial position using the iou of the bboxes
        return Face.bb_intersection_over_union(self.bbox, other_face.bbox) > iou_thres
    
    @staticmethod
    def bb_intersection_over_union(boxA, boxB):
        # Copied directly from TALKNET REPO
        # https://github.com/TaoRuijie/TalkNet-ASD
        #computes the iou of two bboxes
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        iou = interArea / float(boxAArea + boxBArea - interArea)

        return iou
    
    def draw_bbox(self,color=(0,0,0)):

        #draws bboxes on loaded cv2 frame
        #used for debugging bboxes
        if self.cv2 is None:
            Logger.log_error("cv2 Frames Not Loaded")   
        x = int((self.bbox[2] + self.bbox[0])/2)
        y = int((self.bbox[3] + self.bbox[1])/2)
        b_width = self.bbox[2] - self.bbox[0]
        b_height= self.bbox[3] - self.bbox[1]
        Helper.draw_box_on_frame(self.cv2.get_cv2(), (x,y), (b_width, b_height), color=color)



class FacialTrack(Track):
   
    def __init__(self, scene):
        
        super().__init__(scene)

    def contains_face(self, face):
        # determines whether or not face object is inside of facial track 
        # compares face to the last face added to the track
        return self.frames[-1].compare(face)

    def add(self, face):

        if type(face) is not Face:
            Logger.log_warning("non-face Frame added to FacialTrack")

        #adds face to frames
        super().add(face)
    
    @property
    def last_idx(self):
        # gets frame position of last face in track
        if len(self.frames) == 0:
            return -1
        return self.frames[-1].idx
    
    def interp_frames(self):

        """
        Interpolates face across facial track 
        This ensures that there aren't any frame gaps between the start and end positions of the face in the scene
        """
        
        bboxes = np.array([np.array(face.bbox) for face in self.frames])
        frame_nums = np.array([face.idx for face in self.frames])
        conf = np.array([face.conf for face in self.frames])

        dim_funcs = []
        for i in range(4):
            #interpolate each bbox dim using frameNum as input
            interpfn  = interp1d(frame_nums, bboxes[:,i], bounds_error=False, fill_value="extrapolate")
            dim_funcs.append(interpfn)

        #interpolate each conf value using frameNum as input
        conf_func = interp1d(frame_nums, conf, bounds_error=False, fill_value="extrapolate")
        
        #iterates over raw cv2 frames of facial track
        start = self.faces[0].idx
        end = self.faces[-1].idx
        for i,frame in enumerate(self.scene.get_frames(start=start, end=end)):
            
            setinel = False
            for face in self.frames:
                #update bbox of frame to be interpolated value 
                #helps smooth out bbounding box across track
                if face.idx == i + self.scene.frame_start:
                    bbox = []
                    for j in range(4):
                        bbox.append(dim_funcs[j](face.idx))
                    face.set_bbox(bbox)
                    face.conf = conf_func(face.idx)
                    setinel = True
                    break 
            
            if not setinel:
                # if frame not in facial track
                # add it to facial track and use estimated bbox position as position of face in frame
                new_face = Face.init_from_cv2_frame(frame.get_cv2(), i + self.scene.frame_start)
                bbox = []
                conf = conf_func(face.idx)
                for j in range(4):
                    bbox.append(dim_funcs[j](new_face.idx))
                new_face.set_face_detection_args(bbox, conf)
                self.frames.insert(i, new_face)
            
    def is_speaker(self, thresh=.25):
        #denotes whether track is speaking
        #pretty simple heuristic definitely needs updated later
        #just checks to see if person speaking is speaking in more than thresh% of track
        speaking_frames = 0
        for frame in self.frames:
            if frame.get_score() > 0:
                speaking_frames += 1
        return speaking_frames / len(self.frames) > thresh
    
    def get_center_from_none(self):
        #computes the "center" of the track to use cropping
        #returns average center of face in facial track
        x,y = 0,0
        for frame in self.frames:
            center = frame.get_center_from_bbox()
            x += center[0]
            y += center[1]
        x /= len(self.frames)
        y /= len(self.frames) 
        return x,y


    



