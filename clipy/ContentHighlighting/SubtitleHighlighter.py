from .ContentHighlighting import ContentHighlighting
from ..Utilities.SubtitleGenerator import OpenAIWhisper

class SubtitleHighlighter(ContentHighlighting):

    def __init__(self, video_file,approx_length=45, sub_gen = None):
        super().__init__(video_file,approx_length)
        self.sub_gen = sub_gen
        if self.sub_gen is None:
            self.sub_gen = OpenAIWhisper(self.video_file, model_name="tiny.en")

    def highlight_intervals(self):
        self.sub_gen.generate_subtitles()
        timestamps = self.highlight_subtitles()
        return timestamps
    
    def highlight_subtitles(self, subtitles):
        # TODO
        # highlight subtitles
        pass


