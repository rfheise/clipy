from ..Utilities import Timestamp, TimeStamps, Logger, GhostCache, detect_scenes
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
            scenes = self.get_scenes_from_timestamp(t)
            centers = self.detect_center_across_frames(scenes)
            clip = Clip(centers)
            # clip.set_tracks(centers)
            clip.crop()
            videos.append(clip)
        return videos
    
    def create_clip_from_video_file(self, timestamp):
        return Clip.initalize_clip(self.video_file, timestamp, self.cache)

    def crop_frames_around_center(clip, centers):

        #TODO
        # crop clip using the speficied center for each frame
        pass

    def get_scenes_from_timestamp(cls, video_file, timestamp, cache=GhostCache):
        
        #init clip with scenes
        scenes = detect_scenes(video_file, cache=cache)
        # get all scenes in interval
        clip_scenes = []
        for scene in scenes:
            if scene.start <= timestamp.start and scene.end >= timestamp.start:
                clip_scenes.append(scene)
        
        # shortend start and end scene
        clip_scenes[0].trim_scene(timestamp)
        clip_scenes[-1].trim_scene(timestamp)

        return clip_scenes