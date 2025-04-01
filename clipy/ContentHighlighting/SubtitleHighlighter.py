from .ContentHighlighting import ContentHighlighting
from ..Utilities.SubtitleGenerator import OpenAIWhisper
from ..Utilities import GhostCache
from scenedetect import detect, ContentDetector

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

        if self.cache.exists("subtitles"):
            self.sub_gen =  self.cache.get_item("subtitles")
        else:
            self.sub_gen.generate_subtitles()
            self.cache.set_item("subtitles", self.sub_gen, "basic")

        timestamps = self.highlight_subtitles()
        self.cache.set_item("highlight", timestamps, "dev")

        self.detect_scenes()
            
        return timestamps
    
    def detect_scenes(self):
        scene_list = detect('my_video.mp4', ContentDetector())
        for i, scene in enumerate(scene_list):
            print('    Scene %2d: Start %s / Frame %d, End %s / Frame %d' % (
            i+1,
            scene[0].get_timecode(), scene[0].get_frames(),
            scene[1].get_timecode(), scene[1].get_frames(),))

    def highlight_subtitles(self, subtitles):
        # TODO
        # highlight subtitles
        pass


