from ..Utilities import GhostCache 
from .Pizzazz import Pizzazz 
import cv2
from ..Utilities import Config

"""
This module needs to be removed and incorporated into the video cropping process.
Right now the video is cropped and then rescaled. This significantly reduces the quality of the video 
as it's being cropped to a smaller size and then rescaled. This is why some of the output appears pixelated. 
The order needs to be swapped and that will fix this bug.

"""

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