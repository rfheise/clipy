from ..Utilities import GhostCache 
from .Pizzazz import Pizzazz 
import cv2
from ..Utilities import Config

class ResizeCreator(Pizzazz):

    def __init__(self, new_size=(1080,1920), cache=GhostCache()):
        self.cache = cache 
        self.new_size = new_size
    
    def render(self, frames, audio, clip):
        ret = []
        for frame in frames:
            if Config.debug_mode:
                frame = cv2.resize(frame, self.new_size, interpolation=cv2.INTER_NEAREST)
            else:
                frame = cv2.resize(frame, self.new_size, interpolation=cv2.INTER_CUBIC)
            ret.append(frame)
        return ret, audio