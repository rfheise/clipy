import cv2 
from ..Utilities import Timestamp, Logger
import moviepy.editor as mp 
from .AVASD.Face import FacialTrack 
from .Track import Track 

"""
This module represents a video scene object.
It stores the meta data for each "cut" in the video
A video cut is simply the moment when one shot ends and a new one begins—usually because the camera angle or scene changes abruptly.
See Clip.py for more information on data hierarchy.
A scene contains a collection of object tracks and is used to load the raw frames from disk
"""

class Scene():

    counter = 0
    def __init__(self, video_file, start,end, frame_start, frame_end):
        
        #start/end in seconds
        self.start = start 
        self.end = end 

        #start/end in frames
        self.frame_start = frame_start 
        self.frame_end = frame_end
        
        #video path of longform video
        self.video_file = video_file
        
        # used to store raw cv2 frames of the scene
        self.frames = None
        # used to store audio of the scene
        self.audio = None

        #used to create an idx of each scene
        self.idx = Scene.counter 
        Scene.counter += 1

        #used for storing fps property 
        self._fps = None

        #used for keeping track of object tracks
        self.tracks = None
        
        #used for storing the centers for cropping of the scene
        #functionality not really used yet but will be
        self.centers = None

        #scene center
        #cropping position of scene
        #should really be a list of (x,y, timestamp) tuples
        # as you want this to work with multiple objects in a scene
        # right now it assumes one object per scene
        self._scene_center = (None, None)

    @property
    def frame_duration(self):
        #duration of scene in frames
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

        #initializes a scene from pyscene object
        #python scene-detection library is initially used to detect scenes (video cuts)
        return cls(fname, scene[0].get_seconds(), scene[1].get_seconds(),
                   scene[0].get_frames(), scene[1].get_frames())

    def get_timestamp(self):
        return Timestamp(self.start, self.end)
    
    def trim_scene(self, timestamp):
        
        # trims scene so that it is within the timestamp
        if timestamp.start > self.start:
            self.start  = timestamp.start 
            self.frame_start = Scene.get_frame_at_timestamp(self.video_file, timestamp.start)
        
        if timestamp.end < self.end:
            self.end = timestamp.end 
            self.frame_end = Scene.get_frame_at_timestamp(self.video_file, timestamp.end)
    
    def get_frames(self, start = None, end = None, mode="model"):
        
        #maybe the most scuffed thing about this whole project
        #would probably make linus torvalds cry
        #the code itself isn't "terrible" but the loading/freeing paradigm is heavily abused

        # loads frames if not already loaded
        if self.frames is None:
            self.load_frames(mode)

        #load all frames from scene if start and end frame not spcified
        if start is None or end is None:
            return self.frames 
        
        #otherwise only load specified frames
        ret = []
        for i,frames in enumerate(self.frames):
            if i + self.frame_start >= start and i + self.frame_start <= end:
                ret.append(self.frames[i])
        return ret

    def free_frames(self):
        # frees frames from memory
        self.frames = None    

    def load_frames(self, mode = "model"):

        # TODO should have global cv2 object that is managed by clip object
        # only close when clip is done with it
        # just change position to start of scene when loading frames
        # would be more efficient

        self.frames = []
        #opens video with cv2 and indexes it to starting frame
        cap = cv2.VideoCapture(self.video_file)
        cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_start)

        #loads all frames in scene
        for i in range(self.frame_start, self.frame_end):
            ret, frame = cap.read()
            if not ret:
                Logger.log_error("indexed frame not in video")
                exit(4)
            #if mode is model loads frames as RGB 
            #default is BGR
            #TODO mode should be color scheme and not use case
            if mode == "model":
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frames.append(frame)
        #close video file
        cap.release()
    
    def get_audio(self, start=None, end=None):

        # gets audio from scene
        self.load_audio(start, end)
        audio = self.audio 
        #incase I need load-free functionality for audio very 💅 demure
        self.free_audio()

        return audio
    
    def load_audio(self, start, end):
    
        #loads audio for duration of scene 
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
        #may update functionality later to include multiple objects in scene
        for i in range(len(tracks)):
            for j in range(i + 1, len(tracks)):
                if isinstance(tracks[i], type(tracks[j])) is False:
                    Logger.log_error("Tracks not same type")
                    exit(5)

        self.tracks = tracks 
    
    def add_track(self, track):

        # add a track to track list

        #initializes tracks if they aren't yet initalized
        if self.tracks is None:
            self.tracks = []
        self.tracks.append(track)
    
    def __iter__(self):

        #return tracks as iterable object
        return iter(self.get_tracks())
    
    def get_centers_from_facial_tracks(self):

        """
        Returns the center of the scene based on the facial tracks.

        Needs to be reworked because right now this only works if just one person is speaking in the shot.
        Honestly this assumption holds true about ~60% of the time and yields mediocre results
        If multiple people are speaking in the shot, it will just return the center of the scene.


        If one facial track: return center of face
        If one speaker: return center of speaker
        else: just return the center of the frame
    
        Returns
         (int, int): coordinates of the center of the scene
        """

        # honestly this logic should be implemented elsewhere 🤷‍♂️

        # makes sure all facial tracks have been scored
        for track in self.tracks:
            for frame in track.frames:
                if frame.get_score() is None:
                    Logger.log_error("score not processed")
                    exit(3)

        #generates list of all facial tracks that contain a speaker
        speakers = []
        for track in self.tracks:
            if track.is_speaker():
                speakers.append(track)
        
        # if num facial tracks is 1 return center of face 
        if len(self.tracks) == 1:
            return self.tracks[0].get_center()
        
        #if num speakers is 1 return center of speaker
        if len(speakers) == 1:
            return speakers[0].get_center()
        
        #else return center of frame
        return self.tracks[0].get_center_of_frames()
    
    def set_centers(self):
        
        # sets the center of the scene based upon object tracks
        # during the rendering phase the scene is cropped around this point

        #s is a sentinel that is used to check if frame center should be used or not
        s = len(self.tracks) > 0
        for track in self.tracks:
            # if scene is made up of all facial tracks use get_centers_from_facial track method
            if isinstance(track, FacialTrack) is False:
                s = False

        #if facial track are present in scene get the center using the facial tracks
        if s:
            self.centers = [self.get_centers_from_facial_tracks()]
        else:
            # otherwise just return the center of the scene
            self.centers = [self.scene_center]

    def get_center(self):
        #it is done like this because it assumes only one center per scene
        #as I stated above this assumption doesn't always hold true and yields mediocre results

        #gets first center in scene 
        if self.centers is None:
            Logger.log_error("Centers Not Set")
            exit(75)
        return self.centers[0]

    def free_frames_from_tracks(self):
        #frees frames from memory
        self.frames = None
        for track in self:
            track.free_frames()
