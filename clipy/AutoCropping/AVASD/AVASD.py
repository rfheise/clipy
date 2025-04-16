from ...Utilities import GhostCache, Logger, Helper, Timestamp, Profiler, Config
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

"""
    Uses TalkNet for automatically cropping the videos. Takes in the input Clip and processes the location of the active speaker. 
    This is probably the most scuffed logic in the entire codebase. 
    Most if this file is just rewriting the preprocessing steps from the original TalkNet codebase because it was ✨ Hot Garbage ✨. No offense to the original TalkNet author but it looked like he sped through the code to get results as fast as possible. 
    Even though I'm a little harsh on his codebase I really appreciate his research work because TalkNet yields really really good results for AVASD and basically every paper since then on this task has reused his work.
    First the input video is converted to run at 25fps and 16khz audio. This is because the default trained TalkNet model only supports this kind of input. 
    I honestly think you could retrain the model with various audio sampling rates and paddding for the frames but then I would have to put in actual work to re-train the model. 
    Maybe I'll do that in the future but for now this works. 
    Then I loop through all of the frames in the clip and get a list of all the detected faces in each frame. 
    Then I loop through all of the detected faces and generate a facial track across every video cut that contains that face. 
    To determine if a face is in a facial track it just uses some basic logic to detect if the iou of the facial bounding box between other faces in the track is above a threshold. 
    It then takes all facial tracks & their corresponding audio and scores them using the TalkNet model. 
    It stores this information inside of each facial track and this data is later used when rendering the output video.

    If you're curious about how talknet scores the facial tracks try running in debug mode and it will save a video of the bounding boxes to ./debug

    TLDR; 
    Input Video -> Reformats video to run at 25fps & 16000hz -> Detects Faces -> Generates Facial Tracks -> Scores Facial Tracks -> Saves Scores For Rendering

"""

class AVASD(AutoCropper):

    def __init__(self, video_path, clips, face_detection_model=S3FD,avasd_model=TalkNet, cache=GhostCache()):
        
        super().__init__(video_path, clips, cache=cache)

        # face detection model (s3fd)
        self.fdm = face_detection_model(device=Config.device)

        #number of failed detections before face is rejected
        self.num_failed_det = Config.args.num_failed_det

        # min frames in facial track
        self.min_frames_in_track = Config.args.min_frames_in_track

        # avasd model (talknet)
        self.avasd_model = avasd_model(Config.device)
    
    def detect_tracks_in_scenes(self, clip):
        
        # prints timestamp of clip for debugging
        Logger.debug(str(clip.get_timestamp()))

        # if clip is cached don't process it again
        if self.cache.get_item(f"clip-{clip.id}-scenes") is not None:

            scenes = self.cache.get_item(f"clip-{clip.id}-scenes")
            clip.set_scenes(scenes)
            Logger.debug(f"Loading Clip {clip.id} from cache")
            return
        
        #start profilers for debugging
        #facial detection & facial track generation
        Profiler.start("facial detection")
        self.generate_facial_tracks(clip)
        Profiler.stop("facial detection")

        #calls avasd model for scoring
        Profiler.start("speaker detection")
        self.score_tracks(clip)
        Profiler.stop("speaker detection")
        

        # if debug mode is enabled it saves bounding boxes
        if Config.args.save_bboxes:
            Logger.debug(f"Saving Bounding Boxes For Clip")
            os.makedirs("./debug/bboxes", exist_ok=True)
            self.draw_bbox_around_scene( f"./debug/bboxes/bboxes-{clip.id}.mp4", clip)
            clip.reset_frames()

        #cache rendered clip if in debug/dev mode
        self.cache.set_item(f"clip-{clip.id}-scenes", clip.get_scenes(), level="dev")

    def draw_bbox_around_scene(self, fname, clip):

        # loops through all the frames in the scene and draws a bounding box around the face
        for scene in clip.get_scenes():
            for track in scene:
                for frame in track.frames:
                    if type(frame) == Face:
                        # if face detected sets color to green otherwise red
                        color = (0,0,255)
                        if frame.get_score() > 0:
                            color = (0,255,0)
                        frame.draw_bbox(color=color)
        
        # puts all frames in one list
        frames = clip.get_frames()
        
        # writes the frames to a video file
        Helper.write_video(frames, "./.cache/scene.tmp.mp4",fps=scene.fps)
        new_video=mp.VideoFileClip("./.cache/scene.tmp.mp4")
        # loads audio from og clip
        video = mp.VideoFileClip(self.video_file)
        audio = video.audio.subclip(clip.get_start(), clip.get_end())
        new_video.audio = audio
        
        #combines audio and video
        new_video.write_videofile(fname, codec="libx264", audio_codec="aac", logger=None)
        
        #removes tmp file and frames from memory
        os.remove("./.cache/scene.tmp.mp4")
        
        
        

    def score_tracks(self, clip):

        Logger.log("Detecting Speakers In Tracks")

        total = 0
        for scene in clip.get_scenes():
            total += len(scene.tracks)

        # prints this here so it doesn't print for every single track
        if Config.args.save_facial_tracks:
            Logger.debug("Saving Tracks For Faces")
        pbar = tqdm(total=total)

        # loops through all the tracks in the clip and scores them
        d = os.path.join(".cache","preprocessed_clips")
        os.makedirs(d, exist_ok=True)
        tmp_video = os.path.join(d,f"clip-{clip.id}.mp4")
        Helper.preprocess_video(clip.video_file,tmp_video, clip.get_start(), clip.get_end() + 1)
        for tracks in clip.get_scenes():
            for track in tracks:
                
                # only scores facial track
                if type(track) is FacialTrack:
                    score = self.get_score(track, clip, tmp_video)
                    for i,frame in enumerate(track.frames):
                        # smoothing for frame score
                        s = score[max(i - 2, 0):min(i + 3, len(track.frames))]
                        frame.set_score(s.mean())

                pbar.update(1)
        os.remove(tmp_video)

    def generate_facial_tracks(self, clip):
        
        Logger.log("Generating Facial Tracks")

        # detects faces across frames
        scene_faces = self.detect_faces(clip)

       # count of current frame
        count = 0

        for scene in clip.get_scenes():
            facial_tracks = []
            for i in range(scene.frame_duration):
                # frame idx in video file
                frame_idx = i + scene.frame_start

                #makes sure frame idx matches up with face index
                if count + clip.get_start_frame() != frame_idx:
                    Logger.log_error("frame index mismatch")
                    exit(45)

                #faces in current frame
                faces = scene_faces[count]

                count += 1

                #loops across faces and adds them to the facial tracks
                for face in faces:
                    sentinel = False

                    for track in facial_tracks:
                        if track.contains_face(face):
                            track.add(face)
                            sentinel = True
                            break 

                    # if face added to track loop onto next face
                    if sentinel:
                        continue
                    
                    # otherwise create new track
                    facial_tracks.append(FacialTrack(scene))
                    facial_tracks[-1].add(face)
                    
                # keep track only if it meets detection threshold
                # determines number failed detections by comparing last face idx to current idx
                facial_tracks = [track for track in facial_tracks if abs(frame_idx - facial_tracks[-1].last_idx) < self.num_failed_det]
            
            # keep only tracks that meet min frame req
            facial_tracks = [track for track in facial_tracks if len(track) >= self.min_frames_in_track]
            
            if len(facial_tracks) == 0:

                facial_tracks = []

            scene.set_tracks(facial_tracks)

        return clip

    def detect_faces(self, clip):
        
        #gets all bboxes across all frames
        video_shape = clip.get_frames()[0].get_cv2().shape
        video_scale = max(video_shape[1]/720, video_shape[0]/480)

        bboxes = self.fdm.detect_faces(clip,scales = [Config.args.scale_s3fd/video_scale],
                                        conf_th=Config.args.conf_th_s3fd,
                                        min_face_percentage=Config.args.min_face_percentage)
        scene_faces = []
        # gets starting frame idx
        curr_frame = clip.get_start_frame()

        # loads all raw cv2 frames
        frames = [frame for frame in clip.get_frames()]

        #loop through all faces detected in each frame
        for frame_bbox in bboxes:
            faces = []

            for i in range(frame_bbox.shape[0]):
                
                #create a face using the raw frame, bbox, and conf values
                bbox = frame_bbox[i]
                face = Face.init_from_raw_frame(frames[curr_frame - clip.get_start_frame()], curr_frame)
                face.set_face_detection_args(bbox[:-1], bbox[-1])

                faces.append(face)
            
            scene_faces.append(faces)
            curr_frame += 1

        return scene_faces
    

    def get_score(self, track, clip_id, tmp_video):
        
        # gets score of facial track from avasd model
        return self.avasd_model.get_score(track, clip_id, tmp_video)
            

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
