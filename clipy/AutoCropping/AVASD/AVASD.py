from ...Utilities import GhostCache, Logger, Helper
from ..AutoCropper import AutoCropper
from .Face import Face, FacialTrack
from ..Track import Track
from collections import defaultdict
from .s3fd import S3FD
from tqdm import tqdm
import os
import moviepy.editor as mp
import torch
import cv2
import numpy as np 
from .TalkNet import TalkNet

torch.set_num_threads(8)

class AVASD(AutoCropper):

    def __init__(self, video_path, clips, face_detection_model=S3FD,avasd_model=TalkNet, cache=GhostCache()):
        super().__init__(video_path, clips, cache=cache)
        self.fdm = face_detection_model(device=Logger.device)
        #number of failed detections before face is rejected
        self.num_failed_det = 10
        self.min_frames_in_track = 20
        self.facial_tracks = None
        self.avasd_model = avasd_model(Logger.device)
    
    def detect_center_across_frames(self, clip):
        
        self.cache.clear("facial_tracks")
        if self.cache.exists("facial_tracks"):
            self.facial_tracks = self.cache.get_item("facial_tracks")
        else:
            self.facial_tracks = self.generate_facial_tracks(clip)

            # self.draw_bbox_around_facial_tracks('./.cache/tracks')
            # self.draw_bbox_around_scene(f"./.cache/scene-low.mp4")

            #TMP CODE WHILE DEVELOPING
            #NEEDS TO BE REMOVED WHEN DONE
            # self.cache.save("./.cache/fd_test.sav")
            


            self.score_tracks(self.facial_tracks)
            self.cache.set_item("facial_tracks", self.facial_tracks)
            import random
            self.draw_bbox_around_scene(f"./.cache/scene-{random.randint(0,10000)}.mp4")
            return
        #speakers is list of lists of centers in case there are multiple speakers
        
        speakers = self.get_speakers_from_tracks(self.facial_tracks)
        return speakers
    
    def draw_bbox_around_facial_tracks(self, dirname):
        
        os.makedirs(dirname, exist_ok=True)
        count = 0
        for scene in self.facial_tracks:
            for track in scene:
                count += 1
                if type(track) is FacialTrack:
                    track.render_bbox_video(os.path.join(dirname, f"track-{count}.mp4"))

    def draw_bbox_around_scene(self, fname):
        #was really really tired so started to get sloppy around this point
        #definitely needs re-done
        for scene in self.facial_tracks:
            for track in scene:
                track.free_frames()
        for scene in self.facial_tracks:
            for track in scene:
                track.load_frames(mode="render")
                for frame in track.frames:
                    if type(frame) == Face:
                        color = (0,0,255)
                        if track.get_score() > 0:
                            color = (0,255,0)
                        frame.draw_bbox(color=color)
        
        frames = []
        for tracks in self.facial_tracks:
            frames.extend(tracks[0].scene.get_frames())
        Helper.write_video(frames, "./.cache/scene.tmp.mp4")
        new_video=mp.VideoFileClip("./.cache/scene.tmp.mp4")
        video = mp.VideoFileClip(self.video_file)
        audio = video.audio.subclip(self.facial_tracks[0][0].scene.start, self.facial_tracks[-1][0].scene.end)
        new_video.audio = audio
        new_video.write_videofile(fname, codec="libx264", audio_codec="aac")
        os.remove("./.cache/scene.tmp.mp4")
        
        

    def score_tracks(self, facial_tracks):

        for tracks in facial_tracks:
            for track in tracks:
                if type(track) is FacialTrack:
                    print("here")
                    score = self.get_score(track)
                    track.set_score(score)
        
    def get_speakers_from_tracks(facial_tracks):

        #map tracks in scene
        centers = []
        scene_tracks = defaultdict([])
        for track in facial_tracks:
            if track.get_score() is None:
                Logger.error("Score not set")
            scene_tracks[track.scene_id].append(track)
        for key in scene_tracks.keys():
            try:
                scene_tracks[key].sort(key=lambda x:x.score)
            except AttributeError:
                #default track encountered no need to sort
                pass
            #return tracks instead of center
            centers.append(scene_tracks[key][0])
        return centers

    
    def generate_facial_tracks(self, scenes):
        
        if self.cache.exists("gen_facial_tracks"):
            return self.cache.get_item("gen_facial_tracks")

        clip_tracks = []
        Logger.log("Generating Facial Tracks")
        pbar = tqdm(total=self.get_total_frames(scenes))
        for scene in scenes:
            frames =  scene.get_frames()
            facial_tracks = []
            for i, frame in enumerate(frames):
                frame_idx = i + scene.frame_start
                faces = self.detect_faces(frame, frame_idx)
                for face in faces:
                    setinel = False
                    # if facial track exists add it
                    for track in facial_tracks:
                        if track.contains_face(face):
                            track.add(face)
                            s = True
                            break 
                    if setinel:
                        continue
                    
                    # otherwise create new track
                    facial_tracks.append(FacialTrack(scene))
                    facial_tracks[-1].add(face)
                    
                # keep track only if it meets detection threshold
                facial_tracks = [track for track in facial_tracks if abs(frame_idx - facial_tracks[-1].last_idx) < self.num_failed_det]
                pbar.update(1)
            # keep only tracks that meet min frame req
            facial_tracks = [track for track in facial_tracks if len(track) >= self.min_frames_in_track]
            
            #after tracks are processed interp
            #the bboxes to remove gaps between frames
            for track in facial_tracks:
                print(len(track.frames))
                track.interp_frames()
                print(len(track.frames))
            
            if len(facial_tracks) == 0:

                facial_tracks = [Track.init_from_raw_frames(scene, frames)]

            clip_tracks.append(facial_tracks)
            scene.free_frames()
        clip_tracks.sort(key = lambda x:x[0].frames[0].idx)
        self.cache.set_item("gen_facial_tracks",clip_tracks,"dev")
        return clip_tracks

    def crop_frames_around_center(clip, centers):
        #TODO
        # crop clip using the speficied center for each frame
        pass

    def detect_faces(self, frame, frame_idx):
        
        bboxes = self.fdm.detect_faces(frame)
        faces = []
        for bbox in bboxes:
            #possibly cache cv2 frame in face 
            #I guess depends on speed savings as you wouldn't hit disk
            face = Face.init_from_cv2_frame(frame, frame_idx)
            face.set_face_detection_args(bbox[:-1], bbox[-1])
            faces.append(face)

        return faces
    

    def get_score(self, track):
        return self.avasd_model.get_score(track)
            

if __name__ == "__main__":
    from ...Utilities import Cache 
    from ...ContentHighlighting import ChatGPTHighlighter
    video_path = "./videos/films/walk_the_line.mp4"
    cache = Cache(dev=True)
    cache_file = "./.cache/fd_test.sav"
    cache.load(cache_file)
    # cache.clear('highlight')
    # cache.clear('scenes')
    # cache.clear()
    highlighter = ChatGPTHighlighter(video_path,model="gpt-4o", cache=cache, sub_model="turbo")
    intervals = highlighter.highlight_intervals()
    cache.save(cache_file)
    
    #don't cache AVASD quite yet
    cropper = AVASD(video_path, intervals, cache=cache)
    cropper.crop()