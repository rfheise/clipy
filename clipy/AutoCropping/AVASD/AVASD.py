from ...Utilities import GhostCache, Logger, Helper, Timestamp, Profiler
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
import random 

torch.set_num_threads(8)

class AVASD(AutoCropper):

    def __init__(self, video_path, clips, face_detection_model=S3FD,avasd_model=TalkNet, cache=GhostCache()):
        super().__init__(video_path, clips, cache=cache)
        self.fdm = face_detection_model(device=Logger.device)
        #number of failed detections before face is rejected
        self.num_failed_det = 10
        self.min_frames_in_track = 20
        self.avasd_model = avasd_model(Logger.device)
    
    def detect_tracks_in_scenes(self, clip):
        
        Logger.debug(str(clip.get_timestamp()))
        if self.cache.get_item(f"clip-{clip.id}-scenes") is not None:
            scenes = self.cache.get_item(f"clip-{clip.id}-scenes")
            clip.set_scenes(scenes)
            Logger.debug(f"Loading Clip {clip.id} from cache")
            return
        Profiler.start("facial detection")
        self.generate_facial_tracks(clip)
        Profiler.stop("facial detection")
        Profiler.start("speaker detection")
        self.score_tracks(clip.get_scenes(), clip.id)
        Profiler.stop("speaker detection")
        if Logger.debug_mode:
            Logger.debug(f"Saving Bounding Boxes For Clip")
            os.makedirs("./debug/bboxes", exist_ok=True)
            self.draw_bbox_around_scene( f"./debug/bboxes/bboxes-{clip.id}.mp4", clip.get_scenes())
        for scene in clip.get_scenes():
            scene.free_frames_from_tracks()
        self.cache.set_item(f"clip-{clip.id}-scenes", clip.get_scenes(), level="dev")
        
        
    
    def draw_bbox_around_facial_tracks(self, dirname, scenes):
        
        os.makedirs(dirname, exist_ok=True)
        count = 0
        for scene in scenes:
            for track in scene:
                count += 1
                if type(track) is FacialTrack:
                    track.render_bbox_video(os.path.join(dirname, f"track-{count}.mp4"))

    def draw_bbox_around_scene(self, fname, scenes):
        #was really really tired so started to get sloppy around this point
        #definitely needs re-done
        for scene in scenes:
            for track in scene:
                track.free_frames()
        for scene in scenes:
            for track in scene:
                track.load_frames(mode="render")
                for frame in track.frames:
                    if type(frame) == Face:
                        color = (0,0,255)
                        if frame.get_score() > 0:
                            color = (0,255,0)
                        # cv2.putText(frame.cv2, str(frame.get_score()), (int(frame.bbox[0]), int(frame.bbox[1])), cv2.FONT_HERSHEY_SIMPLEX, 1.5, color,1)
                        frame.draw_bbox(color=color)
        
        frames = []
        for scene in scenes:
            frames.extend(scene.get_frames())
        Helper.write_video(frames, "./.cache/scene.tmp.mp4",fps=scene.fps)
        new_video=mp.VideoFileClip("./.cache/scene.tmp.mp4")
        video = mp.VideoFileClip(self.video_file)
        audio = video.audio.subclip(scenes[0].start, scenes[-1].end)
        new_video.audio = audio
        new_video.write_videofile(fname, codec="libx264", audio_codec="aac", logger=None)
        os.remove("./.cache/scene.tmp.mp4")
        
        

    def score_tracks(self, scenes, clip_id=0):
        Logger.log("Detecting Speakers In Tracks")

        total = 0
        for scene in scenes:
            total += len(scene.tracks)
        Logger.debug("Saving Tracks For Faces")
        pbar = tqdm(total=total)
        for tracks in scenes:
            for track in tracks:
                if type(track) is FacialTrack:
                    score = self.get_score(track, clip_id)
                    for i,frame in enumerate(track.frames):
                        s = score[max(i - 2, 0):min(i + 3, len(track.frames))]
                        frame.set_score(s.mean())
                pbar.update(1)

    def generate_facial_tracks(self, clip):
        
        Logger.log("Generating Facial Tracks")
        scenes = clip.get_scenes()
        scene_faces = self.detect_faces(scenes)
        count = 0
        for scene in scenes:
            frames =  scene.get_frames()
            facial_tracks = []
            for i in range(scene.frame_duration):
                frame_idx = i + scene.frame_start

                if count + scenes[0].frame_start != frame_idx:
                    Logger.log_error("frame index mismatch")
                    exit(45)

                # faces = self.detect_faces(frame, frame_idx)
                faces = scene_faces[count]
                count += 1
                for face in faces:
                    setinel = False
                    # if facial track exists add it
                    for track in facial_tracks:
                        if track.contains_face(face):
                            track.add(face)
                            setinel = True
                            break 
                    if setinel:
                        continue
                    
                    # otherwise create new track
                    facial_tracks.append(FacialTrack(scene))
                    facial_tracks[-1].add(face)
                    
                # keep track only if it meets detection threshold
                facial_tracks = [track for track in facial_tracks if abs(frame_idx - facial_tracks[-1].last_idx) < self.num_failed_det]
            # keep only tracks that meet min frame req
            facial_tracks = [track for track in facial_tracks if len(track) >= self.min_frames_in_track]
            
            #after tracks are processed interp
            #the bboxes to remove gaps between frames
            for track in facial_tracks:
                track.interp_frames()
            
            if len(facial_tracks) == 0:

                facial_tracks = [Track.init_from_raw_frames(scene, frames)]

            scene.set_tracks(facial_tracks)
            scene.free_frames()
        return scenes

    def detect_faces(self, scenes):
        
        bboxes = self.fdm.detect_faces(scenes)
        scene_faces = []
        curr_frame = scenes[0].frame_start
        frames = [frame for scene in scenes for frame in scene.get_frames()]
        for frame_bbox in bboxes:
            faces = []
            for i in range(frame_bbox.shape[0]):
                #possibly cache cv2 frame in face 
                #I guess depends on speed savings as you wouldn't hit disk
                bbox = frame_bbox[i]
                face = Face.init_from_cv2_frame(frames[curr_frame - scenes[0].frame_start], curr_frame)
                face.set_face_detection_args(bbox[:-1], bbox[-1])

                faces.append(face)
            
            scene_faces.append(faces)
            curr_frame += 1
        for scene in scenes:
            scene.free_frames()
        return scene_faces
    

    def get_score(self, track, clip_id):
        return self.avasd_model.get_score(track, clip_id)
            

if __name__ == "__main__":
    from ...Utilities import Cache 
    from ...ContentHighlighting import ChatGPTHighlighter
    video_path = "./videos/other/walk_the_line_25_16.mp4"
    cache = Cache(dev=True)
    cache_file = "./.cache/fd_test.sav"
    cache.set_save_file(cache_file)
    cache.load(cache_file)
    cache.clear("videos")
    cache.clear(f"clip-0-scenes")
    cache.clear("bboxes")
    Profiler.start()
    # cache.clear('highlight')
    # cache.clear('scenes')
    # cache.clear()
    # highlighter = ChatGPTHighlighter(video_path,model="gpt-4o", cache=cache, sub_model="turbo")
    # intervals = highlighter.highlight_intervals()
    # intervals.insert(0,Timestamp(1498,1546))
    # cache.save(cache_file)
    intervals = [Timestamp(1498,1546)]
    #don't cache AVASD quite yet
    cropper = AVASD(video_path, intervals, cache=cache)
    cropper.crop()
    cache.save(cache_file)
    Profiler.stop()