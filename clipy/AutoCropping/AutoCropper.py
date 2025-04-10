from ..Utilities import Timestamp, TimeStamps, Logger, GhostCache, detect_scenes, Profiler
from .Clip import Clip
from .Scene import Scene

class AutoCropper():

    def __init__(self, video_file, timestamps, cache=GhostCache()):

        self.video_file = video_file
        self.timestamps = timestamps
        self.cache = cache 

    def detect_tracks_in_scenes(self, clip):

        #TODO
        # detect center across all frames in video file 
        # to be implemented by detection engine
        pass 

    def crop(self):
        videos = []
        if self.cache.exists("videos"):
            return self.cache.get_item("videos")
        Profiler.start("crop")
        for t in self.timestamps:
            clip = Clip.init_from_timestamp(self.video_file, t, cache=self.cache)
            self.cache.save()
            Logger.new_line()
            Logger.log(f"Runnning AutoCropper on Clip {clip.id}")
            self.detect_tracks_in_scenes(clip)
            # clip.set_tracks(centers)
            clip.crop()
            videos.append(clip)
            Logger.new_line()
        Profiler.stop("crop")
        self.cache.set_item("videos", videos, "dev")
        return videos
    