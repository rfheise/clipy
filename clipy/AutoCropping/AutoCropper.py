from ..Utilities import Timestamp, TimeStamps, Logger, GhostCache
from .Clip import Clip

class AutoCropper():

    def __init__(self, video_file, timestamps, cache=GhostCache):

        self.video_file = video_file
        self.timestamps = timestamps
        self.cache = cache 
    
    def detect_center_across_frames(self, clip):
        #TODO
        # detect center across all frames in video file 
        # to be implemented by detection engine
        pass 

    def crop(self):
        videos = []
        for t in self.timestamps:
            clip = self.create_clip_from_video_file(t)
            centers = self.detect_center_across_frames(clip)
            clip.set_tracks(centers)
            clip.crop()
            videos.append(clip)
        return videos
    
    def create_clip_from_video_file(self, timestamp):
        return Clip.initalize_clip(self.video_file, timestamp)

    def crop_frames_around_center(clip, centers):
        #TODO
        # crop clip using the speficied center for each frame
        pass