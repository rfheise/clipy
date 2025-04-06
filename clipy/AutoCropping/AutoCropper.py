from ..Utilities import Timestamp, TimeStamps, Logger, GhostCache, detect_scenes
from .Clip import Clip

class AutoCropper():

    def __init__(self, video_file, timestamps, cache=GhostCache()):

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
            scenes = self.get_scenes_from_timestamp(self.video_file, t, self.cache)
            centers = self.detect_center_across_frames(scenes)
            clip = Clip(centers)
            # clip.set_tracks(centers)
            clip.crop()
            videos.append(clip)
        return videos
    
    def create_clip_from_video_file(self, timestamp):
        return Clip.initalize_clip(self.video_file, timestamp, cache=self.cache)

    def crop_frames_around_center(clip, centers):

        #TODO
        # crop clip using the speficied center for each frame
        pass
    
    @staticmethod
    def get_scenes_from_timestamp(video_file, timestamp, cache=GhostCache()):
        #init clip with scenes
        scenes = detect_scenes(video_file, cache=cache)
        # get all scenes in interval
        clip_scenes = []
        for scene in scenes:
            if (scene.start >= timestamp.start and scene.start < timestamp.end) or \
                (scene.end <= timestamp.end and scene.start > timestamp.start) or \
                (scene.start < timestamp.start and scene.end > timestamp.end):
                clip_scenes.append(scene)

        # shortend start and end scene
        clip_scenes[0].trim_scene(timestamp)
        clip_scenes[-1].trim_scene(timestamp)

        return clip_scenes
    
    @staticmethod
    def get_total_frames(scenes):
        total_frames = 0
        for scene in scenes:
            total_frames += scene.frame_end - scene.frame_start + 1
        return total_frames