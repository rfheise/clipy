from ..Utilities import Logger
from ..Utilities import detect_scenes, Timestamp,TimeStamps

"""
ContentHighlighting.py

This module highlights the most interesting moments in a video.
This module servers as an abstract class for the Content Highlighting section of the pipeline.
The module contains several utility functions that can help inherited implementations. 

Usage Example:
    highlighter =  ContentHighlighter(video_path)
    intervals = highlighter.highlight_intervals()
"""

class ContentHighlighting():

    def __init__(self, video_file, approx_length=45, cache=None,
                    min_duration=30, max_duration=60):

        self.video_file = video_file
        self.approx_length = approx_length
        self.cache = cache
        self.min_duration = min_duration
        self.max_duration = max_duration

    def highlight_intervals(self):
        """
        This method should be implemented in the inherited class.
        It returns the most interesting timestamps in the video.

        (Timestamps):list of timestamps that will be turned into video clips
        """
        pass

    def adjust_timestamps_to_scenes(self, timestamps):
        """Takes timestamps and adjusts them so that matchup with cuts in the video. 

        Args:
            timestamps (TimeStamps): list of input timestamps to be adjusted

        Returns:
            TimeStamps: Adjusted video timestamps
        """

        scenes = detect_scenes(self.video_file, cache=self.cache)
        scenes = TimeStamps([Timestamp(scene[0].get_seconds(), scene[1].get_seconds()) for scene in scenes])
        #could be improved but fine for now
        #since it isn't a bottleneck
        ts = TimeStamps()
        for timestamp in timestamps:
            t = self.adjust_timestamp_to_scenes(scenes, timestamp)
            Logger.debug(t)
            ts.add_timestamp(t)
        return ts
    
    def adjust_timestamp_to_scenes(self, scenes, timestamp):
        """Adjusts a single timestamp to the closest scenes in the video.

        Args:
            scenes (scenedetect scene object): list of scenes in the video
            timestamp (Timestamp): timestamp to be adjusted

        Returns:
            Timestamp: adjusted timestamp
        """
        new_stamp = Timestamp(timestamp.start,timestamp.end)
        for scene in scenes:
            if scene.start <= timestamp.start and scene.end >= timestamp.start:
                #don't create a new timestamp if only scene is longer than max duration
                if scene.end - scene.start >= self.max_duration:
                    Logger.debug("Scene Duration Too Long")
                #make sure clip has at least one scene
                new_stamp.start = scene.start
                new_stamp.end = scene.end 
            
            n_dur = scene.end - new_stamp.start
            if n_dur < 0:
                continue
            dur = new_stamp.duration
            # print(abs(n_dur - self.approx_length) - abs(dur - self.approx_length))
            if n_dur >= self.min_duration and n_dur <= self.max_duration \
                and abs(n_dur - self.approx_length) < abs(dur - self.approx_length):
                new_stamp.end = scene.end
            if n_dur > self.max_duration:
                break
        return new_stamp


            

            
            
            