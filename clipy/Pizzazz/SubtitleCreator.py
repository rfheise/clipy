from .Pizzazz import Pizzazz 
from ..Utilities import OpenAIWhisper, GhostCache, Helper
import random

class SubtitleCreator(Pizzazz):

    def __init__(self, subgen=None, cache = GhostCache()):
        super().__init__(cache)
        self.subgen = subgen
        self.scale = None
        
    
    def init_subgen(self, clip):

        if self.subgen is None:

            if self.cache.exists("subtitles"):
                self.subgen = self.cache.get_item("subtitles")
                return 
            
            self.subgen = OpenAIWhisper(clip.video_file, "tiny.en")
        

    def render(self, frames, audio, clip):

        self.init_subgen(clip)
        self.color = random.choice(Helper.bright_colors)
        # self.color = Helper.Color.GOLDENROD.value
        # self.color = Helper.Color.YELLOW.value
        subtitles = self.subgen.get_subtitles(clip.get_timestamp())
        frame_start = clip.get_start_frame()
        fps = clip.get_scenes()[0].fps
        for i, frame in enumerate(frames):
            if self.scale is None:

                self.scale = frame.shape[0] / 480

            frame_idx = i + frame_start 
            for subtitle in subtitles:
                if (subtitle.timestamp.get_start_frame(fps) <= frame_idx\
                    and subtitle.timestamp.get_end_frame(fps) > frame_idx):
                    frames[i] = self.write(frame, subtitle.text)
        return frames, audio

    def write(self, frame, text):

        #TODO write subtitles to frame
        
        max_width = frame.shape[1] - 20 * self.scale  # Set maximum width (with a margin)
        font_path = './fonts/Roboto.ttf'
        font_size = 20 * self.scale
        
        #get bottom corner
        position = (int(frame.shape[1]/2), 3*int(frame.shape[0]/4))  # Starting position (x, y)

        frame = Helper.draw_wrapped_text(frame, text, position, font_path, font_size,
                                          self.color, max_width, self.scale, border_thickness=1)
        return frame
            
            

