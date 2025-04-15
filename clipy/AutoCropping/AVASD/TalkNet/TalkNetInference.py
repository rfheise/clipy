from .model import talkNet
import cv2
import numpy as np
from python_speech_features import mfcc
import math 
from scipy.io import wavfile
import torch 
import os
from ....Utilities import Logger, Helper, Config
import moviepy.editor as mp
import random
import subprocess

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

    def get_score(self, track, clip_id=0):

        # generates random value for facial track debugging
        track.rand = random.randint(0,10**8)
        
        video = self.load_frames_for_avasd(track)
        audio = self.load_audio_for_avasd(track)

        # if Config.debug_mode:
        #     # saves video of facial track for debugging
        #     self.write_out(video, track.scene.get_audio(), track.scene.fps, track, clip_id)
        
        score = self.eval_model(video, audio, track.scene.fps)

        return score
    
    def write_out(self, video, audio,fps, track, clip_id):

        #writes the facial track to a file

        os.makedirs(f"./debug/talknet-inputs/{clip_id}/{track.scene.idx}", exist_ok=True)
        out_video = f"./debug/talknet-inputs/{clip_id}/{track.scene.idx}/video.mp4"

        Helper.write_video(video, "./debug/scene-track.tmp.mp4",fps=fps)

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
        length = video.shape[0]
    
        #trim audio to match video length
        audio = audio[:int(length * av_scale)]

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
    
    def load_audio_for_avasd(self, track):


        #start/end times of the audio in audio frames
        start = track.frames[0].idx/track.scene.fps
        end = (track.frames[-1].idx + 1)/track.scene.fps

        # re-renders the audio to make sure it is in a wav file at 16000hz

        command = ("ffmpeg -y -i %s -async 1 -ac 1 -vn -acodec pcm_s16le -ar 16000 -threads %d -ss %.3f -to %.3f %s -loglevel panic" % \
		      (track.scene.video_file, 2, start, end, "./.cache/scene-audio.wav"))
        output = subprocess.call(command, shell=True, stdout=None)
        sample_rate, audio = wavfile.read( "./.cache/scene-audio.wav")
        
        #mel-frequency cepstral coefficient for audio input
        return mfcc(audio, 16000, numcep = 13, winlen = 0.025, winstep = 0.010)
    
    def load_frames_for_avasd(self, track):
        
        #frees potentially modified frames
        #kind of hacky and can probably can be removed but whatever
        track.free_frames()

        #loads the frames from the disk as cv2 image
        track.load_frames()
    
        raw_frames = []
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

            #weird scaling thing the original author did
            #since I'm reusing his pretrained model 
            #I have to preprocess my data in the exact same way
            cs = .4
            bsi = int(bs * (1 + 2 * cs))
            raw = frame.cv2.get_cv2()
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