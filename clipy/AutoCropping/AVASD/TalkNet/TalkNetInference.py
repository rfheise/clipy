from .model import talkNet
import cv2
import numpy as np
from python_speech_features import mfcc
import math 

class TalkNetInference():

    def __init__(self, device):
        self.model = talkNet(device)
        self.winstep = 0.010

    def get_score(self, track):
        self.load_frames_for_avasd(track)
        video = np.array([frame.crop_cv2() for frame in track.frames])
        audio = self.load_audio_for_avasd(track)
        score = self.eval_model(video, audio, track.scene.fps)
    
    def eval_model(self, video, audio, fps):
        self.model.eval()
        durationSet = {1,2,3,4,5,6}
        allScore = [] # Evaluation use TalkNet
        #total duration of clip
        length = video.shape[0]/fps
        for duration in durationSet:
            batchSize = int(math.ceil(length / duration))
            scores = []
            with torch.no_grad():
                for i in range(batchSize):
                    audio_scale = int(1/self.winstep)
                    inputA = torch.FloatTensor(audio[i * duration * audio_scale:(i+1) * duration * audio_scale,:]).unsqueeze(0).cuda()
                    inputV = torch.FloatTensor(video[i * duration * int(fps): (i+1) * duration * int(fps),:,:]).unsqueeze(0).cuda()
                    embedA = self.model.forward_audio_frontend(inputA)
                    embedV = self.model.forward_visual_frontend(inputV)	
                    embedA, embedV = self.model.forward_cross_attention(embedA, embedV)
                    out = self.model.forward_audio_visual_backend(embedA, embedV)
                    score = self.lossAV.forward(out, labels = None)
                    scores.extend(score)
            allScore.append(scores)
        allScore = np.round((np.mean(np.array(allScore), axis = 0)), 1).astype(float)
        return allScore
    
    def load_audio_for_avasd(self, track):

        #vibe coded with gpt 

        audio = track.scene.get_audio()
        # Extract the audio as a NumPy array at 16000 Hz (matching the expected sample rate).
        audio = audio.to_soundarray(fps=16000)

        # If the audio is stereo, convert it to mono by averaging the channels.
        if audio.ndim == 2 and audio.shape[1] == 2:
            audio = audio.mean(axis=1)

        # Compute MFCC features using the extracted audio.
        audioFeature = mfcc(audio, samplerate=16000, numcep=13, winlen=0.025, winstep=self.winstep)
        
    def load_frames_for_avasd(self, track):
        track.free_frames()
        track.load_frames()
        for frame in track.frame:
            frame.cv2 = cv2.cvtColor(frame.cv2, cv2.COLOR_BGR2GRAY)
            frame.cv2 = cv2.resize(frame, (244, 244))
            #idk why he only uses half the resized frame?
            #probably for efficiency
            #need to read paper
            frame.cv2 = frame.cv2[int(112-(112/2)):int(112+(112/2)), int(112-(112/2)):int(112+(112/2))]
