import cv2 
from ..Utilities import Timestamp, Logger
import moviepy.editor as mp 
from .AVASD.Face import FacialTrack 
from .Track import Track 

class Scene():

    counter = 0
    def __init__(self, video_file, start,end, frame_start, frame_end):
        self.start = start 
        self.end = end 
        self.frame_start = frame_start 
        self.frame_end = frame_end
        self.video_file = video_file
        self.cap = None
        self.frames = None
        self.audio = None
        self.idx = Scene.counter 
        Scene.counter += 1
        self._fps = None
        self.tracks = None
        self.centers = None
        self._scene_center = (None, None)

    @property
    def frame_duration(self):
        return self.frame_end - self.frame_start
    
    @property
    def scene_center(self):
        if self._scene_center[0] is None:
            # Open the video file.
            cap = cv2.VideoCapture(self.video_file)

            # Get the frame at the start of the scene.
            cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_start)
            ret, frame = cap.read()
            if not ret:
                Logger.log_error("indexed frame not in video")
                exit(4)
            self._scene_center = (frame.shape[1] // 2, frame.shape[0] // 2)
            cap.release()
        return self._scene_center
    
    @property
    def fps(self):
        if self._fps is None:
            # Open the video file.
            cap = cv2.VideoCapture(self.video_file)

            # Get frames per second (FPS) of the video.
            self._fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()
        return self._fps

    @classmethod
    def init_from_pyscene(cls, fname, scene):
        return cls(fname, scene[0].get_seconds(), scene[1].get_seconds(),
                   scene[0].get_frames(), scene[1].get_frames())

    def get_timestamp(self):
        return Timestamp(self.start, self.end)
    
    def trim_scene(self, timestamp):
        
        if timestamp.start > self.start:
            self.start  = timestamp.start 
            self.frame_start = Scene.get_frame_at_timestamp(self.video_file, timestamp.start)
        if timestamp.end < self.end:
            self.end = timestamp.end 
            self.frame_end = Scene.get_frame_at_timestamp(self.video_file, timestamp.end)
    
    def get_frames(self, start = None, end = None, mode="model"):
        
        if self.frames is None:
            self.load_frames(mode)
        if start is None or end is None:
            return self.frames 
        ret = []
        for i,frames in enumerate(self.frames):
            if i + self.frame_start >= start and i + self.frame_start <= end:
                ret.append(self.frames[i])
        return ret

    def free_frames(self):
        self.frames = None    

    def load_frames(self, mode = "model"):
        self.frames = []
        cap = cv2.VideoCapture(self.video_file)
        # Logger.debug(f"{self.start}, {self.end}, {self.frame_start}, {self.frame_end}")
        cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_start)
        for i in range(self.frame_start, self.frame_end):
            ret, frame = cap.read()
            if not ret:
                Logger.log_error("indexed frame not in video")
                exit(4)
            if mode == "model":
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frames.append(frame)
        cap.release()
    
    def get_audio(self, start=None, end=None):
        self.load_audio(start, end)
        audio = self.audio 
        #incase I need load-free functionality
        self.free_audio()
        return audio
    
    def load_audio(self, start, end):
        if start is None:
            start = self.start 
        if end is None:
            end = self.end
        video = mp.VideoFileClip(self.video_file)
        self.audio = video.audio.subclip(start, end)

    def free_audio(self):
        self.audio = None

    @staticmethod
    def get_frame_at_timestamp(video_path, timestamp_sec):
        #vibe coded with chatgpt


        # Open the video file.
        cap = cv2.VideoCapture(video_path)

        # Get frames per second (FPS) of the video.
        fps = cap.get(cv2.CAP_PROP_FPS)
        # Calculate the frame number.
        frame_number = round(timestamp_sec * fps)


        return frame_number

    def get_tracks(self):
        if self.tracks is None:
            Logger.log_warning("Tracks not initialized")
        return self.tracks
    
    def set_tracks(self, tracks):
        
        #ensure all tracks are the same type 
        for i in range(len(tracks)):
            for j in range(i + 1, len(tracks)):
                if isinstance(tracks[i], type(tracks[j])) is False:
                    Logger.log_error("Tracks not same type")
                    exit(5)
        self.tracks = tracks 
    
    def add_track(self, track):
        if self.tracks is None:
            self.tracks = []
        self.tracks.append(track)
    
    def __iter__(self):
        return iter(self.get_tracks())
    
    def get_centers_from_facial_tracks(self):
        num_speakers = 0
        for track in self.tracks:
            for frame in track.frames:
                if frame.get_score() is None:
                    Logger.log_error("score not processed")
                    exit(3)
        speakers = []
        for track in self.tracks:
            if track.is_speaker():
                speakers.append(track)
                num_speakers += 1
        if len(self.tracks) == 1:
            return self.tracks[0].get_center()
        if num_speakers == 1:
            return speakers[0].get_center()
        return self.tracks[0].get_center_of_frames()
    
    def set_centers(self):

        s = len(self.tracks) > 0
        for track in self.tracks:
            if isinstance(track, FacialTrack) is False:
                s = False
        if s:
            self.centers = [self.get_centers_from_facial_tracks()]
        else:
            self.centers = [self.scene_center]

    def get_center(self):

        #gets first center in scene 
        if self.centers is None:
            Logger.log_error("Centers Not Set")
            exit(75)
        return self.centers[0]

    def free_frames_from_tracks(self):
        self.frames = None
        for track in self:
            track.free_frames()
