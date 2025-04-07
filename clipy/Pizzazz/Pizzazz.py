from ..Utilities import GhostCache 

class Pizzazz():

    def __init__(self, cache=GhostCache()):
        self.cache = cache 
    
    def render(frames, audio, clip):
        #TODO
        # to be overwritten by inherited classes
        # return modified frames and audio
        return frames, audio