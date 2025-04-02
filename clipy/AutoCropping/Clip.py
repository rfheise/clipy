from .Frame import FrameStamp
class Clip():

    def __init__(self, frame_stamp):

        self.tracks = None 
        self.frame_stamp = frame_stamp
        self.scenes = None 
    
    def set_tracks(self, tracks):
        self.tracks = tracks

    def render(self, fname):

        #TODO
        # render clip and store it at fname 
        pass 

    @classmethod
    def initialize_clip(cls, t, timestamp):
        # TODO
        # generate Clip object
        # add clip scenes
        pass 

    def load_scenes(self):
        #TODO
        #load scenes for clip 
        #create scene object for better control
        pass