from .Pizzazz import Pizzazz 
from ..Utilities import OpenAIWhisper, GhostCache, Helper, FrameOp
import random

"""

Adds subtitles to short

"""
class SubtitleFrameOp(FrameOp.FrameOp):

    arg_format = [FrameOp.Arg("text"), FrameOp.Arg("color"), FrameOp.Arg("scale")]

    def process_frame(self, frame):
        # basically just a wrapper for the Helper.draw_wrapped text method
        # could optionally make a lot of these Config options
        
        max_width = frame.shape[1] - 20 * self.scale  # Set maximum width (with a margin)
        font_path = './fonts/Roboto.ttf'
        font_size = 20 * self.scale
        
        #get bottom corner
        position = (int(frame.shape[1]/2), 3*int(frame.shape[0]/4))  # Starting position (x, y)

        frame = Helper.draw_wrapped_text(frame, self.text, position, font_path, font_size,
                                          self.color, max_width, self.scale, border_thickness=1)
        return frame

class SubtitleCreator(Pizzazz):

    def __init__(self, subgen=None, cache = GhostCache()):
        super().__init__(cache)
        self.subgen = subgen
        self.scale = None
        
    
    def init_subgen(self, clip):
        
        #initializes the subtitle model 
        #if the subtitles have already been generated for the entire video 
        #earlier in the pipeline just used the cached subtitles
        if self.subgen is None:
            
            if self.cache.exists("subtitles"):
                self.subgen = self.cache.get_item("subtitles")
                return 
            
            self.subgen = OpenAIWhisper(clip.video_file, "tiny.en")
        

    def render(self, frames, audio, clip):

        #Renders subtitles on top of each video clip
        # initializes subtitle generator
        self.init_subgen(clip)

        #selects random bright color as subtitle color
        self.color = random.choice(Helper.bright_colors)

        #loads subtitles
        #will pull from cache if they are cached
        subtitles = self.subgen.get_subtitles(clip.get_timestamp())

        #iterates over frames
        #if frame is within the timestamp of a subtitle add that subtitle on top of the frame
        frame_start = clip.get_start_frame()
        fps = clip.get_scenes()[0].fps
        for i, frame in enumerate(frames):
            if self.scale is None:
                
                #I set the font size using 480p video as reference
                #Scales font to og size
                self.scale = frame.render().shape[0] / 480

            frame_idx = i + frame_start 
            for subtitle in subtitles:
                if (subtitle.timestamp.get_start_frame(fps) <= frame_idx\
                    and subtitle.timestamp.get_end_frame(fps) > frame_idx):
                    frame.add_op(SubtitleFrameOp(text=subtitle.text, color=self.color, scale = self.scale))
        self.scale = None
        return frames, audio

        
            

