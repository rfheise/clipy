from .ContentHighlighting import ContentHighlighting
from ..Utilities.SubtitleGenerator import OpenAIWhisper
from ..Utilities import GhostCache, Logger, Profiler

"""
SubtitleHighlighter.py

This module servers as an abstract class for ContentHighlighters that rely on subtititles alone.
The module contains several utility functions that can help inherited implementations. 

"""

class SubtitleHighlighter(ContentHighlighting):

    def __init__(self, video_file,approx_length=45, sub_gen = None, cache=GhostCache()):
        super().__init__(video_file,approx_length)

        #subgen is the subtitle generator
        #default is open ai whisper
        
        self.sub_gen = sub_gen
        if self.sub_gen is None:
            self.sub_gen = OpenAIWhisper(self.video_file, model_name="tiny.en")
        self.cache = cache

    def highlight_intervals(self):
        
        if self.cache.exists("highlight"):
            return self.cache.get_item("highlight")
        Profiler.start("subtitle highlighting")
        Profiler.start("subtitle generation")
        if self.cache.exists("subtitles"):
            self.sub_gen =  self.cache.get_item("subtitles")
        else:
            self.sub_gen.generate_subtitles()
            self.cache.set_item("subtitles", self.sub_gen, "basic")
        Profiler.stop("subtitle generation")
        timestamps = self.highlight_subtitles()
        timestamps = self.adjust_timestamps_to_scenes(timestamps)
        # Logger.debug(timestamps)
        self.cache.set_item("highlight", timestamps, "dev")
        Profiler.stop("subtitle highlighting")
        return timestamps

    def highlight_subtitles(self, subtitles):
        # TODO
        # highlight subtitles
        pass


