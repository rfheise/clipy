

class SubtitleGenerator():

    def __init__(self, fname, subtitle_interval=30):
        self.subtitles = []
        self.fname = fname 
        self.subtitle_interval = subtitle_interval
    
    def generate_subtitles(self):
        #TODO generate subtitles from the video
        pass
    
    def get_subtitles(self):
        return self.subtitles
    
    def add_subtitle(self, subtitle):
        self.subtitles.append(subtitle)
    
    def add_subtitles(self, subtitles):
        for sub in subtitles:
            self.add_subtitle(sub) 
    
    def merge(self, other):
        #TODO merge the subtitles of various segments & remove duplicates
        pass

    def to_srt(self, out_file):
        #TODO write the subtitles to an srt file
        pass

class Subtitle():
    
    def __init__(self, text, timestamp):
        self.text = text
        self.timestamp = timestamp
    
    def __str__(self):
        return f"{self.timestamp}: {self.text}"
    
