from ..Track import Track 
from ..Frame import Frame 
from ...Utilities import Logger
import cv2 
import moviepy.editor as mp
import os

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
    
    def draw_bbox(self):
        if self.cv2 is None:
            Logger.log_error("cv2 Frames Not Loaded")   
        x = int((self.bbox[2] + self.bbox[0])/2)
        y = int((self.bbox[3] + self.bbox[1])/2)
        b_width = self.bbox[2] - self.bbox[0]
        b_height= self.bbox[3] - self.bbox[1]
        draw_box_on_frame(self.cv2, (x,y), (b_width, b_height))



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
    
    
    def render_bbox_video(self, fname):

        self.load_frames(mode = "render")
        for face in self.frames:
            face.draw_bbox()
        write_video(self.scene.frames, fname + ".tmp.mp4")
        self.free_frames()
        new_video=mp.VideoFileClip(fname + ".tmp.mp4")
        new_video.audio = self.scene.get_audio()
        new_video.write_videofile(fname, codec="libx264", audio_codec="aac")
        os.remove(fname + ".tmp.mp4")
        self.scene.free_audio()



def draw_box_on_frame(frame, center, box_size=(100, 100), color=(0, 0, 0), thickness=2):
    """
    Draws a rectangle (box) on the frame with the center at 'center'.
    
    Parameters:
      frame (numpy.ndarray): The input image (frame).
      center (tuple): The (x, y) coordinates of the center of the box.
      box_size (tuple): The (width, height) of the box.
      color (tuple): The BGR color for the box.
      thickness (int): The thickness of the box lines.
    
    Returns:
      numpy.ndarray: The modified frame with the drawn box.
    """
    x, y = center
    width, height = box_size
    # Calculate top-left and bottom-right coordinates from the center point.
    top_left = (int(x - width / 2), int(y - height / 2))
    bottom_right = (int(x + width / 2), int(y + height / 2))
    # Make a copy so the original frame is not modified.
    # frame_with_box = frame.copy()
    frame_with_box = frame
    cv2.rectangle(frame_with_box, top_left, bottom_right, color, thickness)
    return frame_with_box

def write_video(frames, output_path, fps=24):
    """
    Writes a list of frames (numpy arrays) to a video file.
    
    Parameters:
      frames (list): List of frames (numpy arrays).
      output_path (str): Path to the output video file.
      fps (int): Frames per second for the output video.
    """
    # Get dimensions from the first frame.
    height, width = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # You can choose another codec if desired.
    video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    for frame in frames:
        video_writer.write(frame)
    
    video_writer.release()
