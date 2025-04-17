from .model import talkNet
import cv2
import numpy as np
from python_speech_features import mfcc
import math 
from scipy.io import wavfile
import torch 
import os
from ....Utilities import Logger, Helper, Config, Profiler
import moviepy.editor as mp
import random
import subprocess
from scipy.interpolate import interp1d

"""
Code for running TalkNet ASD on a set of images. 
This is a wrapper I made for running the core TalkNet model so that it would work with my codebase. 


"""


class TalkNetInference():

    PATH_WEIGHT = os.path.join(os.path.dirname(__file__), "talknet.model")

    def __init__(self, device):
        #loads core talknet model
        self.model = talkNet(device)

        #downloads pre-trained weights if they don't exist
        #weights are personally hosted on cloudflare at files.quettacompute.com
        if not os.path.exists(TalkNetInference.PATH_WEIGHT):
            Logger.log("Downloading TalkNet Model Weights")
            Helper.download_cf("talknet.model", TalkNetInference.PATH_WEIGHT)
        
        #load the pretrained weights
        self.model.loadParameters(TalkNetInference.PATH_WEIGHT)

        self.winstep = 0.010
        self.device = device

    def get_score(self, track, clip, processed_video):

        # generates random value for facial track debugging
        track.rand = random.randint(0,10**8)
        
        video = self.load_frames_for_avasd(track, clip, processed_video)
        audio = self.load_audio_for_avasd(track, clip, processed_video)
        if Config.args.save_facial_tracks:
            # saves video of facial track for debugging
            self.write_out(video, track.scene.get_audio(), track.scene.fps, track, clip.id)
        score = self.eval_model(video, audio, self.get_fps(processed_video))
        score = self.interp_scores(score, track, clip)
        
        return score
    
    def interp_scores(self,scores, track,clip):
        start = (track.frames[0].idx - clip.get_start_frame())/track.scene.fps
        end = (track.frames[-1].idx - clip.get_start_frame())/track.scene.fps

        times = np.linspace(start, end, num=scores.shape[0], endpoint=False)
        interp_func = interp1d(times, scores,bounds_error=False, fill_value="extrapolate")
        times = np.linspace(start, end, num=len(track.frames), endpoint=False)
        return interp_func(times)
    
    def write_out(self, video, audio,fps, track, clip_id):

        #writes the facial track to a file

        os.makedirs(f"./debug/talknet-inputs/{clip_id}/{track.scene.idx}", exist_ok=True)
        out_video = f"./debug/talknet-inputs/{clip_id}/{track.scene.idx}/video.mp4"

        Helper.write_video_raw(video, "./debug/scene-track.tmp.mp4",fps=fps)

        new_video=mp.VideoFileClip("./debug/scene-track.tmp.mp4")
        new_video.audio = audio
        
        new_video.write_videofile(out_video, codec="libx264", audio_codec="aac",logger=None)
        os.remove("./debug/scene-track.tmp.mp4")

    def eval_model(self, video, audio, fps):

        self.model.eval()
        
        #used in the og implementation
        #averages scores across several duration input sizes
        #these are in seconds
        durationSet = {1,2,3,4,5,6}

        allScore = [] 
        fps = round(fps) #number of frames per second
        audio_scale = round(1/self.winstep) #number of audio frames per second
        av_scale = audio_scale/fps #numer of audio frames per video frame

        #total duration of clip
        length = min(video.shape[0]/fps, audio.shape[0]/audio_scale)
        length = int(length * fps)
        #trim audio to match video length
        audio = audio[:int(length * av_scale)]
        video = video[:int(length)]

        #trim video to match audio length


        for duration in durationSet:
            duration = duration * fps # duration of batch in frames
            batchSize = int(math.ceil(length/duration)) # batch size in frames

            scores = []
            with torch.no_grad():
                end = None
                for i in range(batchSize + 1):

                    inputV = torch.FloatTensor(video[i*duration : (i+1) * duration,:,:]).unsqueeze(0).to(self.device)
                    
                    audio_dur = round(inputV.shape[1]/fps * audio_scale) #computes audio chunk start/end
                    if end is None:
                        start = 0
                    else:
                        start = end
                    end = start + audio_dur
                    
                    inputA = torch.FloatTensor(audio[start:end,:]).unsqueeze(0).to(self.device)
                    padding_v_dims = 0

                    # potential padding that may or may not be needed in the future
                    # padding_v_dims = max(0, int(math.ceil(inputA.shape[1]/4) - inputV.shape[1]))
                    # padding = torch.zeros((1,padding_v_dims, inputV.shape[2], inputV.shape[3])).to(self.device)
                    # inputV = torch.cat((inputV, padding),dim=1)
                    # padding_a_dims = max(0, int(inputV.shape[1]*av_scale) - inputA.shape[1])
                    # padding = torch.zeros((1, padding_a_dims, inputA.shape[2])).to(self.device)
                    # inputA = torch.cat((inputA, padding), dim=1)

                    #if the input is empty, break
                    if (inputA.shape[1] == 0 and inputV.shape[1] == 0):
                        break
                    
                    #create embeddings
                    embedA = self.model.model.forward_audio_frontend(inputA)
                    embedV = self.model.model.forward_visual_frontend(inputV)	
                    
                    #run cross attention on embeddings
                    embedA, embedV = self.model.model.forward_cross_attention(embedA, embedV)
                    
                    #run self attention on cross attention outputs
                    out = self.model.model.forward_audio_visual_backend(embedA, embedV)

                    #determine whether track contains active speaker
                    score = self.model.lossAV.forward(out, labels = None)
                    score = score[:score.shape[0]-padding_v_dims]
                    scores.append(score)

            scores = np.concatenate([arr for arr in scores])
            allScore.append(scores)

        # average duration scores for each frame
        allScore = np.round((np.mean(np.array(allScore), axis = 0)), 1).astype(float)
        return allScore
    
    def load_audio_for_avasd(self, track,clip, video_file):


        #start/end times of the audio in audio frames
        start = (track.frames[0].idx - clip.get_start_frame())/track.scene.fps
        end = (track.frames[-1].idx - clip.get_start_frame())/track.scene.fps

        # re-renders the audio to make sure it is in a wav file at 16000hz

        command = ("ffmpeg -y -i %s -async 1 -ac 1 -vn -acodec pcm_s16le -ar 16000 -b:a 32k -threads %d -ss %.3f -to %.3f %s -loglevel panic" % \
		      (video_file, 2, start, end, "./.cache/scene-audio.wav"))
        output = subprocess.call(command, shell=True, stdout=None)
        sample_rate, audio = wavfile.read( "./.cache/scene-audio.wav")
        
        #mel-frequency cepstral coefficient for audio input
        return mfcc(audio, 16000, numcep = 13, winlen = 0.025, winstep = 0.010)
    
    def get_fps(self, video_file):
        cap = cv2.VideoCapture(video_file)

        # Get frames per second (FPS) of the video.
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        return fps 
    
    def get_new_bboxes(self, faces, new_frames, start, end):

        # get start times 
        
        times = np.linspace(start, end, num=len(faces), endpoint=False)
        bboxes = np.array([np.array(face.bbox) for face in faces])
        inter_funcs = []
        for i in range(4):
            inter_funcs.append(interp1d(times, bboxes[:,i], bounds_error=False, fill_value="extrapolate"))
        
        new_bboxes = []
        times = np.linspace(start, end, num=len(new_frames), endpoint=False)
        for time in times:
            new_bbox = []
            for i in range(4):
                if i % 2 == 0:
                    new_bbox.append(inter_funcs[i](time) * new_frames[0].shape[1]/faces[0].width)
                else:
                    new_bbox.append(inter_funcs[i](time)* new_frames[0].shape[0]/faces[0].height) 
            new_bboxes.append(np.array(new_bbox))
        return new_bboxes

    def get_frames(self, video_path, start_sec, end_sec):
        """
        Extract frames from a video between start_sec and end_sec.

        Parameters:
            video_path (str): Path to the video file.
            start_sec (float): Start time in seconds.
            end_sec (float): End time in seconds.

        Returns:
            frames (list): List of frames (numpy arrays) captured between the given timestamps.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Error opening video file")

        # Set the starting position (in milliseconds)
        cap.set(cv2.CAP_PROP_POS_MSEC, start_sec * 1000)

        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Get current time in milliseconds from the capture device
            current_time_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
            # If we have passed the end timestamp, break out of the loop.
            if current_time_ms > end_sec * 1000:
                break

            frames.append(frame)

        cap.release()
        return frames
        
    def load_frames_for_avasd(self, track, clip, processed_video):
        

        raw_frames = []
        start = (track.frames[0].idx - clip.get_start_frame())/track.scene.fps
        end = (track.frames[-1].idx - clip.get_start_frame())/track.scene.fps
        new_frames = self.get_frames(processed_video, start, end)
        new_bboxes= self.get_new_bboxes(track.frames, new_frames, start, end)
        for frame in track.frames:

            #update bbox as square
            bbox = []
            bbox_height = abs(frame.bbox[1] - frame.bbox[3])
            bbox_width = abs(frame.bbox[0] - frame.bbox[2])
            bs = max(bbox_height, bbox_width)/2
            x = (frame.bbox[0] + frame.bbox[2])/2
            y = (frame.bbox[1] + frame.bbox[3])/2
            bbox.append(x - bbox_width/2)
            bbox.append(y - bbox_height/2)
            bbox.append(x + bbox_width/2)
            bbox.append(y + bbox_height/2)
            frame.set_bbox(bbox)

        #rescale bboxes 
        for i in range(len(new_frames)):

            #update bbox as square
            bbox = []
            bbox_height = abs(new_bboxes[i][1] - new_bboxes[i][3])
            bbox_width = abs(new_bboxes[i][0] - new_bboxes[i][2])
            bs = max(bbox_height, bbox_width)/2
            x = (new_bboxes[i][0] + new_bboxes[i][2])/2
            y = (new_bboxes[i][1] + new_bboxes[i][3])/2
            bbox.append(x - bbox_width/2)
            bbox.append(y - bbox_height/2)
            bbox.append(x + bbox_width/2)
            bbox.append(y + bbox_height/2)

            #weird scaling thing the original author did
            #since I'm reusing his pretrained model 
            #I have to preprocess my data in the exact same way
            cs = .4
            bsi = int(bs * (1 + 2 * cs))
            raw = new_frames[i]
            raw = np.pad(raw, ((bsi,bsi), (bsi,bsi), (0, 0)), 'constant', constant_values=(110, 110))
            my = y + bsi 
            mx = x + bsi

            #makes sure new bbox is within the bounds of the image
            ys = max(int(my-bs),0)
            ye = min(int(my+bs*(1+2*cs)), raw.shape[0])
            xs = max(int(mx-bs*(1+cs)),0)
            xe = min(int(mx+bs*(1+cs)),raw.shape[1])

            if xs == xe:
                if xe == 0:
                    xe = 1 
                if xs == raw.shape[1]:
                    xs = raw.shape[1] - 1
            if ys == ye:
                if ys == raw.shape[0]:
                    ys = raw.shape[0]  -1 
                if ye == 0:
                    ye = 1

            raw = raw[ys:ye, xs:xe]

            # resize face so it can be used as input to the model
            raw = cv2.resize(raw, (224, 224))

            #convert to grayscale for efficiency
            raw = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
            
            #one more resize for good measure
            #tbh idk why this is here and I probably don't need it
            #but don't feel like removing it
            raw = cv2.resize(raw, (224,224))
            
            #idk why he only uses half the face
            #probably for efficiency as this focuses on the lips
            raw = raw[int(112-(112/2)):int(112+(112/2)), int(112-(112/2)):int(112+(112/2))]
            raw_frames.append(raw)
        # return preprocessed frames from clip
        return np.array(raw_frames)