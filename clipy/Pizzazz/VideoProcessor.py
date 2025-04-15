import os 
from ..Utilities import Logger, Helper, GhostCache, Profiler
import moviepy.editor as mp


"""
VideoProcessor.py 

This module takes in the Clip objects returned by the auto cropper and renders them into an actual short.


"""


class VideoProcessor:
    def __init__(self, videos, cache=GhostCache()):
        self.videos = videos
        self.pizzazz_list = []
        self.cache = cache

    def add_pizzazz(self, pizzazz):
        self.pizzazz_list.append(pizzazz)
    
    def save_to_file(self, fname, frames, audio, fps):
        
        #saves process frames and video to output clip

        #saves frames to temp video file
        #basically this is kind of a hack that just loads the raw 
        #frames in to a movie editor object
        # probably an easier way to do this
        Helper.write_video(frames, "./scene.tmp.mp4",fps=fps)
        new_video=mp.VideoFileClip("./scene.tmp.mp4")

        #adds audio to loaded movie py frame video
        new_video.audio = audio

        #writes video to output file
        new_video.write_videofile(fname, codec="libx264",
                                  ffmpeg_params=["-crf", "18", "-preset", "medium"],
                                   audio_codec="aac", logger=None)

    def render(self, output_dir="clips"):
        os.makedirs(output_dir, exist_ok=True)
        Profiler.start("render")

        #loops over clip objects
        for video in self.videos:
            outfile = f"clip-{video.id}.mp4"
            Logger.new_line()
            Logger.log(f"Rendering {outfile}")
            
            #actually crops the raw video frames and resizes them to a short
            frames,audio = video.render()

            #adds additional pizzazz specified by the user
            for pizzazz in self.pizzazz_list:
                frames, audio = pizzazz.render(frames, audio, video)

            #writes rendered clip to output file
            self.save_to_file(os.path.join(output_dir, f"clip-{video.id}.mp4"),
                              frames, audio, video.get_scenes()[0].fps)
            
            #frees frames from memory
            video.free_frames()
            
            print(f"Processed video saved at: {outfile}")

        Profiler.stop("render")