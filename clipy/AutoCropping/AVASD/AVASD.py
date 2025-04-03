from ...Utilities import GhostCache, Logger
from ..AutoCropper import AutoCropper
from .Face import Face, FacialTrack 
from ..Track import Track
from collections import defaultdict
from .s3fd import S3FD
from tqdm import tqdm

import torch
torch.set_num_threads(8)

class AVASD(AutoCropper):

    def __init__(self, video_path, clips, face_detection_model=S3FD, cache=GhostCache()):
        super().__init__(video_path, clips, cache=cache)
        self.fdm = face_detection_model(device=Logger.device)
        #number of failed detections before face is rejected
        self.num_failed_det = 10
        self.min_frames_in_track = 20
        self.facial_tracks = None
    
    def detect_center_across_frames(self, clip):
        
        if self.cache.exists("facial_tracks"):
            self.facial_tracks = self.cache.get_item("facial_tracks")
        else:
            self.facial_tracks = self.generate_facial_tracks(clip)
            print("exiting normally")
            exit(0)
            self.score_tracks(self.facial_tracks)
            self.cache.set_item("facial_tracks", self.facial_tracks)
        #speakers is list of lists of centers in case there are multiple speakers
        speakers = self.get_speakers_from_tracks(self.facial_tracks)
        return speakers
    
    def score_tracks(self, facial_tracks):

        for track in facial_tracks:
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

                    # if facial track exists add it
                    for track in facial_tracks:
                        if track.contains_face(face):
                            track.add(face)
                            continue 
                    
                    # otherwise create new track
                    facial_tracks.append(FacialTrack(scene))
                    facial_tracks[-1].add(face)
                    
                # keep track only if it meets detection threshold
                facial_tracks = [track for track in facial_tracks if abs(frame_idx - facial_tracks[-1].last_idx) < self.num_failed_det]
                pbar.update(1)
            # keep only tracks that meet min frame req
            facial_tracks = [track for track in facial_tracks if len(track) >= self.min_frames_in_track]
            
            if len(facial_tracks) == 0:

                facial_tracks = [Track.init_from_raw_frames(scene, frames)]
        
            clip_tracks.append(facial_tracks)
            scene.free_frames()
        clip_tracks.sort(key = lambda x:x.frames[0].idx)
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
    
if __name__ == "__main__":
    from ...Utilities import Cache 
    from ...ContentHighlighting import ChatGPTHighlighter
    video_path = "./videos/films/walk_the_line.mp4"
    cache = Cache(dev=True)
    cache_file = "./.cache/fd_test.sav"
    cache.load(cache_file)
    # cache.clear('highlight')
    # cache.clear('scenes')
    highlighter = ChatGPTHighlighter(video_path,model="gpt-4o-mini", cache=cache)
    intervals = highlighter.highlight_intervals()
    cache.save(cache_file)
    print(cache.exists("scenes"))
    #don't cache AVASD quite yet
    cropper = AVASD(video_path, intervals, cache=cache)
    cropper.crop()