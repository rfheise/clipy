from scenedetect import detect, ContentDetector, open_video
from ..SubtitleGenerator.Timestamps import Timestamp, TimeStamps
from ..Logging.Logger import Logger 
from scenedetect import VideoManager, SceneManager
from ..Caching.Cache import GhostCache
import cv2
import moviepy.editor as mp

def detect_scenes(fname, threshold=10, cache=GhostCache):
    # video = open_video(fname)
    # scene_manager = SceneManager()
    # scene_manager.add_detector(
    #     ContentDetector(threshold=threshold,min_scene_len=10)
    #     )
    if cache.exists("scenes"):
        scenes = cache.get_item("scenes")
        return scenes
    Logger.log("Detecting Scenes")
    scene_list = detect(fname, ContentDetector(threshold=threshold,min_scene_len=10,
                                            #    frame_window=3,
                                                # min_content_val=10
                                                ),show_progress=True)
    # scene_list = scene_manager.detect_scenes(video, show_progress=True)
    scenes = [Scene.init_from_pyscene(fname, scene) for scene in scene_list]
    scenes.sort(key=lambda x:x.start)
    cache.set_item('scenes', scenes, "basic")
    return scenes


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
    
    def get_frames(self, mode="model"):
        if self.frames is None:
            self.load_frames(mode)
        return self.frames 

    def free_frames(self):
        self.frames = None    

    def load_frames(self, mode = "model"):
        self.frames = []
        cap = cv2.VideoCapture(self.video_file)
        Logger.debug(f"{self.start}, {self.end}, {self.frame_start}, {self.frame_end}")
        cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_start)
        for i in range(self.frame_start, self.frame_end + 1):
            ret, frame = cap.read()
            if not ret:
                Logger.log_error("indexed frame not in video")
                exit(4)
            if mode == "model":
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frames.append(frame)
        cap.release()
    
    def get_audio(self):
        if self.audio is None:
            self.load_audio()
        return self.audio
    
    def load_audio(self):
        video = mp.VideoFileClip(self.video_file)
        self.audio = video.audio.subclip(self.start, self.end)

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

        cap.release()

        return frame_number