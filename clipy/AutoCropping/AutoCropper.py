from ..Utilities import Timestamp, TimeStamps, Logger, GhostCache, detect_scenes, Profiler
from .Clip import Clip
from .Scene import Scene


"""
AutoCropper.py

This module generates the Clip object for each short and loads it's cropping metadata
This metadata is then use to actually crop the clip during the video processing stage of the pipeline.
This module servers as an abstract class for the Auto Cropping section of the pipeline.
It contains several utility functions that can help inherited implementations. 

This is probably the most scuffed logic in the code and needs reworked.

Usage Example:
    cropper = AutoCropper(video_path, intervals)
    clips = cropper.crop()
"""

class AutoCropper():

    def __init__(self, video_file, timestamps, cache=GhostCache()):

        self.video_file = video_file
        self.timestamps = timestamps
        self.cache = cache 

    def detect_tracks_in_scenes(self, clip):

        """
        detects object tracks (Track.py) across all scenes in video clip
        stores metadata about tracks in for each scene (Scene.py) in clip (Clip.py)
        to be implemented by detection inherited class
        """

        pass 

    def crop(self):
        """
        Creates a clip object for each timestamp interval
        Detects object tracks in each clip and saves information about each object track
        it then uses this information to detect the center of each scene in every clip 
        these centers are then used to render the clip during the Video Processing phase
        """
        videos = []
        
        #returns rendered videos if they're in the cache
        if self.cache.exists("videos"):
            return self.cache.get_item("videos")
        
        Profiler.start("crop")

        for t in self.timestamps:

            #initializes clip from video file & timestamp
            clip = Clip.init_from_timestamp(self.video_file, t, cache=self.cache)

            Logger.new_line()
            Logger.log(f"Runnning AutoCropper on Clip {clip.id}")
            
            #stores center cropping metadata in clip object
            self.detect_tracks_in_scenes(clip)
            
            # uses cropping metadata to update the center of every scene in each clip
            # for more info see Clip.py & Scene.py
            clip.crop()
            videos.append(clip)
            Logger.new_line()


        Profiler.stop("crop")
        # update cache with processed video clips
        self.cache.set_item("videos", videos, "dev")

        return videos
    