from ..Utilities import GhostCache 
from .Pizzazz import Pizzazz 
import cv2

class ResizeCreator(Pizzazz):

    def __init__(self, new_size=(1080,1920), cache=GhostCache()):
        self.cache = cache 
        self.new_size = new_size
    
    def render(self, frames, audio, clip):
        ret = []
        for frame in frames:
            # Resize the frame to 1280x720
            frame = cv2.resize(frame, self.new_size, interpolation=cv2.INTER_LINEAR)
            ret.append(frame)
        return ret, audio