

class Track():


    def __init__(self, scene_id):
        self.scene_id = []
        self.frames = []
        self.start = None
        self.end = None 

    def add_frame(self, frame):

        if self.start is None:
            self.start = frame
        self.end = frame 
        self.frames.add(frame)
    
    #add artificial end
    def set_end(self, frame):
        self.end=frame 
    
    #add artificial start 
    def set_start(self, frame):
        self.start = frame 
    
    def crop(self):
        # TODO
        # implement crop for custom tracks
        # if crop not set don't do anything just add the whole
        # thing resized the video 
        pass 

    @classmethod
    def init_from_scene(cls, scene):
        #TODO
        pass