import os 
from ..Utilities import Logger, Helper, GhostCache
import moviepy.editor as mp

class VideoProcessor:
    def __init__(self, videos, cache=GhostCache()):
        self.videos = videos
        self.pizzazz_list = []
        self.cache = cache

    def add_pizzazz(self, pizzazz):
        self.pizzazz_list.append(pizzazz)
    
    def save_to_file(self, fname, frames, audio, fps):
        # print(len(frames))
        Helper.write_video(frames, "./scene.tmp.mp4",fps=fps)
        new_video=mp.VideoFileClip("./scene.tmp.mp4")
        new_video.audio = audio
        new_video.write_videofile(fname, codec="libx264", audio_codec="aac", logger=None)
        # os.remove("./scene.tmp.mp4")

    def render(self, output_dir="clips"):
        os.makedirs(output_dir, exist_ok=True)
        for video in self.videos:
            outfile = f"clip-{video.id}.mp4"
            Logger.new_line()
            Logger.log(f"Rendering {outfile}")
            frames,audio = video.render()
            for pizzazz in self.pizzazz_list:
                frames, audio = pizzazz.render(frames, audio, video)
            self.save_to_file(os.path.join(output_dir, f"clip-{video.id}.mp4"),
                              frames, audio, video.get_scenes()[0].fps)
            print(f"Processed video saved at: {outfile}")