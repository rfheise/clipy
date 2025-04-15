from ..Utilities import GhostCache 


"""
Pizzazz.py
This module is an abstract class for extra elements that need to be added to the output video.
Each inherited class must implement the render function. This function takes in the current audio and video frames and outputs the new pizzazzed audio and video.
Examples of Pizzazz:
    * Subtitle Overlay
    * Music based on mood of clip
    * Subtitles based upon the current speaker
        * Future implementations could use cached outputs of AVASD model for speaker diarization
    * Etc 
"""

class Pizzazz():

    def __init__(self, cache=GhostCache()):
        self.cache = cache 
    
    def render(self, frames, audio, clip):
        #TODO
        # to be overwritten by inherited classes
        # return modified frames and audio
        return frames, audio