from ..Track import Track 
from ..Frame import Frame 
from ...Utilities import Logger, Helper
import cv2 
import moviepy.editor as mp
import os
from scipy.interpolate import interp1d
import numpy as np 

class Face(Frame):
    
    def __init__(self, idx, center, width, height):
        super().__init__(idx, center, width, height)
        self.bbox = None 
        self.conf = None
    
    def crop_cv2(self):
        if self.cv2 is None:
            Logger.log_error("cv2 not loaded")
            exit(2)
        self.cv2 = self.cv2[int(self.bbox[0]):int(self.bbox[2]),int(self.bbox[1]):int(self.bbox[3])]
        return self.cv2 
    
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
    
    def draw_bbox(self,color=(0,0,0)):
        if self.cv2 is None:
            Logger.log_error("cv2 Frames Not Loaded")   
        x = int((self.bbox[2] + self.bbox[0])/2)
        y = int((self.bbox[3] + self.bbox[1])/2)
        b_width = self.bbox[2] - self.bbox[0]
        b_height= self.bbox[3] - self.bbox[1]
        Helper.draw_box_on_frame(self.cv2, (x,y), (b_width, b_height), color=color)



class FacialTrack(Track):
   
    def __init__(self, scene):
        
        super().__init__(scene)
        self.score = None 

    def set_score(self, score):
        self.score = score
    
    def get_score(self):
        if self.score is None:
            Logger.log_error("score not processed")
            exit(3)
        return self.score

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
    
    def render_bbox_video(self, fname):

        self.load_frames(mode = "render")
        for face in self.frames:
            face.draw_bbox()
        Helper.write_video(self.scene.frames, fname + ".tmp.mp4")
        self.free_frames()
        new_video=mp.VideoFileClip(fname + ".tmp.mp4")
        new_video.audio = self.scene.get_audio()
        new_video.write_videofile(fname, codec="libx264", audio_codec="aac")
        os.remove(fname + ".tmp.mp4")
        self.scene.free_audio()
    
    def interp_frames(self):

        bboxes = np.array([np.array(face.bbox) for face in self.frames])
        frame_nums = np.array([face.idx for face in self.frames])
        conf = np.array([face.conf for face in self.frames])

        dim_funcs = []
        for i in range(4):
            #interp dim along bbox
            interpfn  = interp1d(frame_nums, bboxes[:,i], bounds_error=False, fill_value="extrapolate")
            dim_funcs.append(interpfn)
    
        conf_func = interp1d(frame_nums, conf, bounds_error=False, fill_value="extrapolate")
        
        for i,frame in enumerate(self.scene.get_frames()):
            
            setinel = False
            for face in self.frames:
                
                if face.idx == i + self.scene.frame_start:
                    for j in range(4):
                        face.bbox[j] = dim_funcs[j](face.idx)
                    face.conf = conf_func(face.idx)
                    setinel = True
                    break 
            if not setinel:
            
                new_face = Face.init_from_cv2_frame(frame, i + self.scene.frame_start)
                bbox = []
                conf = conf_func(face.idx)
                for j in range(4):
                    bbox.append(dim_funcs[j](new_face.idx))
                new_face.set_face_detection_args(bbox, conf)
                self.frames.insert(i, new_face)
            
            
    



