from .Frame import Framestamp
from ..Utilities import detect_scenes, GhostCache, Logger

class Clip():

    def __init__(self, video_file, frame_stamp):

        self.tracks = None 
        self.frame_stamp = frame_stamp
        self.video_file = video_file
    
    def set_tracks(self, tracks):
        self.tracks = tracks

    def render(self, fname):

        #TODO
        # render clip and store it at fname 

        pass 