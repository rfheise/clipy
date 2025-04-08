from .ContentHighlighting import ContentHighlighting
from ..Utilities.SubtitleGenerator import OpenAIWhisper
from ..Utilities import GhostCache, Logger, Profiler


class SubtitleHighlighter(ContentHighlighting):

    def __init__(self, video_file,approx_length=45, sub_gen = None, cache=GhostCache()):
        super().__init__(video_file,approx_length)
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
        Profiler.stop("subtitle hightlighting")
        return timestamps

    def highlight_subtitles(self, subtitles):
        # TODO
        # highlight subtitles
        pass


