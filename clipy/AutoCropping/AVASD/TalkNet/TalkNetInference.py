from .model import talkNet
import cv2
import numpy as np
from python_speech_features import mfcc
import math 
from scipy.io import wavfile
import torch 
import os
from ....Utilities import Logger

class TalkNetInference():
    PATH_WEIGHT = os.path.join(os.path.dirname(__file__), "talknet.model")
    def __init__(self, device):
        self.model = talkNet(device)
        if Logger.device == "cuda":
            self.model.loadParameters(TalkNetInference.PATH_WEIGHT)
        self.winstep = 0.010
        self.device = device

    def get_score(self, track):
        video = self.load_frames_for_avasd(track)
        audio = self.load_audio_for_avasd(track)
        score = self.eval_model(video, audio, track.scene.fps)
        return score
    
    def eval_model(self, video, audio, fps):
        self.model.eval()
        durationSet = {1,2,3,4,5,6}
        allScore = [] # Evaluation use TalkNet
        #total duration of clip
        length = min(int((audio.shape[0] - audio.shape[0] % 4) /(1/self.winstep)), int(video.shape[0] / fps))
        # video = [:round]
        audio = audio[:int(length * (1/self.winstep)),:]
        video = video[:int(length * fps),:,:]
        model_fps  = 25
        for duration in durationSet:
            batchSize = int(math.ceil(length / duration))
            scores = []
            with torch.no_grad():
                for i in range(batchSize):
                    audio_scale = round(1/self.winstep)
                    inputA = torch.FloatTensor(audio[i * duration * audio_scale:(i+1) * duration * audio_scale,:]).unsqueeze(0).to(self.device)
                    inputV = torch.FloatTensor(video[i * int(duration * fps): (i+1) * int(duration * fps),:,:]).unsqueeze(0).to(self.device)
                    padding_v_dims = max(0, inputA.shape[1]//4 - inputV.shape[1])
                    padding = torch.zeros((1,padding_v_dims, inputV.shape[2], inputV.shape[3])).to(self.device)
                    inputV = torch.cat((inputV, padding),dim=1)
                    padding_a_dims = max(0, inputV.shape[1]*4 - inputA.shape[1])
                    padding = torch.zeros((1, padding_a_dims, inputA.shape[2])).to(self.device)
                    inputA = torch.cat((inputA, padding), dim=1)

                    embedA = self.model.model.forward_audio_frontend(inputA)
                    embedV = self.model.model.forward_visual_frontend(inputV)	

                    embedA, embedV = self.model.model.forward_cross_attention(embedA, embedV)
                    out = self.model.model.forward_audio_visual_backend(embedA, embedV)
                    score = self.model.lossAV.forward(out, labels = None)
                    scores.extend(score)
            allScore.append(np.array(scores).mean())
        # allScore = np.round((np.mean(np.array(allScore), axis = 0)), 1).astype(float)
        return np.array(allScore).mean()
    
    def load_audio_for_avasd(self, track):

        #vibe coded with gpt and it doesn't fucking work 🙄

        audio = track.scene.get_audio()
        # # Extract the audio as a NumPy array at 16000 Hz (matching the expected sample rate).
        # audio = audio.to_soundarray(fps=track.scene.fps)
        audio.write_audiofile("./.cache/tmp_output.wav")
        _, audio = wavfile.read("./.cache/tmp_output.wav")
        audioFeature = mfcc(audio, 16000, numcep = 13, winlen = 0.025, winstep = 0.010)
        return audioFeature
    
    def load_frames_for_avasd(self, track):
        track.free_frames()
        track.load_frames()
        # cs  = .4
        # bs  = max() # Detection box size
		# bsi = int(bs * (1 + 2 * cs))  # Pad videos by this amount 
		# image = cv2.imread(flist[frame])
		# frame = numpy.pad(image, ((bsi,bsi), (bsi,bsi), (0, 0)), 'constant', constant_values=(110, 110))
		# my  = dets['y'][fidx] + bsi  # BBox center Y
		# mx  = dets['x'][fidx] + bsi  # BBox center X
		# face = frame[int(my-bs):int(my+bs*(1+2*cs)),int(mx-bs*(1+cs)):int(mx+bs*(1+cs))]
		# vOut.write(cv2.resize(face, (224, 224)))
        for frame in track.frames:
            cs = .4
            bbox_height = abs(frame.bbox[1] - frame.bbox[3])
            bbox_width = abs(frame.bbox[0] - frame.bbox[2])
            bs = max(bbox_height, bbox_width)/2
            x = (frame.bbox[0] + frame.bbox[2])/2
            y = (frame.bbox[1] + frame.bbox[3])/2
            #update bbox as square
            bbox = []
            bbox.append(x - bbox_width/2)
            bbox.append(y - bbox_height/2)
            bbox.append(x + bbox_width/2)
            bbox.append(y + bbox_height/2)
            # frame.bbox = bbox
            if Logger.debug:
                os.makedirs(f"./.cache/talknet-inputs/{track.scene.idx}", exist_ok=True)
                cv2.imwrite(f"./.cache/talknet-inputs/{track.scene.idx}/{frame.idx}.jpg", frame.cv2)
            frame.cv2 = frame.crop_cv2()
            # bsi = int(bs * (1 + 2 * cs))
            # frame.cv2 = np.pad(frame.cv2, ((bsi,bsi), (bsi,bsi), (0, 0)), 'constant', constant_values=(110, 110))
            # my = y + bsi 
            # mx = x + bsi
            # frame.cv2 = frame.cv2[int(my-bs):int(my+bs*(1+2*cs)),int(mx-bs*(1+cs)):int(mx+bs*(1+cs))]
            frame.cv2 = cv2.cvtColor(frame.cv2, cv2.COLOR_BGR2GRAY)
            # print(frame.cv2.shape)
            frame.cv2 = cv2.resize(frame.cv2, (244, 244))
            #idk why he only uses half the resized frame?
            #probably for efficiency
            #need to read paper
            # frame.cv2 = frame.cv2[int(112-(112/2)):int(112+(112/2)), int(112-(112/2)):int(112+(112/2))]
            #resize in case crop messed it up
            # frame.cv2 = frame.cv2.resize(frame.cv2, (112,112))
            
            # if Logger.debug:
            #     os.makedirs(f"./.cache/talknet-inputs/{track.scene.idx}", exist_ok=True)
            #     cv2.imwrite(f"./.cache/talknet-inputs/{track.scene.idx}/{frame.idx}.jpg", frame.cv2)
        exit()

        return np.array([frame.cv2 for frame in track.frames])