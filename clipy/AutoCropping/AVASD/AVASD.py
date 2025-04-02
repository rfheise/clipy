from ...Utilities import GhostCache, Logger
from ..AutoCropper import AutoCropper
from .Face import Face, FacialTrack 
from ..Track import Track
from collections import defaultdict
from ..FaceDetection.s3fd import S3FD

class AVASD(AutoCropper):

    def __init__(self, video_path, clips, face_detection_model=S3FD, cache=GhostCache):
        super().__init__(video_path, clips, cache)
        self.fdm = face_detection_model(device=Logger.device)
        #number of failed detections before face is rejected
        self.num_failed_det = 10
        self.min_frames_in_track = 20
        self.facial_tracks = None
    
    def detect_center_across_frames(self, clip):
        
        if self.cache.exists("facial_tracks"):
            self.facial_tracks = self.cache.get_item("facial_tracks")
        else:
            self.facial_tracks = self.get_facial_tracks(clip)
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
            


    
    def generate_facial_tracks(self, clip):

        clip_tracks = []
        for scene in clip.get_scenes():
            for frame in scene.get_frames():
                faces = self.detect_faces(frame)
                for face in faces:

                    # if facial track exists add it
                    for track in facial_tracks:
                        if track.contains_face(face):
                            track.add(face)
                            continue 
                    
                    # otherwise create new track
                    facial_tracks.append(FacialTrack(scene.initial_frame, scene.indx))
                    facial_tracks[-1].add(face)
                    
                # keep track only if it meets detection threshold
                facial_tracks = [track for track in facial_tracks if abs(frame.id - facial_tracks[-1].last_idx) < self.num_failed_det]
            scene.free_frames()
            # keep only tracks that meet min frame req
            facial_tracks = [track for track in facial_tracks if len(track) >= self.min_frames_in_track]
            facial_tracks.audio = scene.get_audio()
            if len(facial_tracks) == 0:
                #TODO initialize default track params
                facial_tracks = [Track.init_from_scene(scene)]

        clip_tracks.sort(key = lambda x:x.initial_frame)
        return clip_tracks

    def crop_frames_around_center(clip, centers):
        #TODO
        # crop clip using the speficied center for each frame
        pass

    def detect_faces(self, frame):
        
        if frame.cv2 is None:
            Logger.log_error("CV2 Frames Not Loaded")
            exit(3)
        bboxes = self.fdm(frame.cv2)
        faces = []
        for bbox in bboxes:
            face = Face.init_from_frame(frame)
            face.set_face_detection_args(bbox[:-1], bbox[-1])
            faces.append(face)
        return faces
        
