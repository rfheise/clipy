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



class TalkNetInference():

    PATH_WEIGHT = os.path.join(os.path.dirname(__file__), "talknet.model")

    def __init__(self, device):
        self.model = talkNet(device)
        if not os.path.exists(TalkNetInference.PATH_WEIGHT):
            Logger.log("Downloading TalkNet Model Weights")
            Helper.download_cf("talknet.model", TalkNetInference.PATH_WEIGHT)
        self.model.loadParameters(TalkNetInference.PATH_WEIGHT)
        self.winstep = 0.010
        self.device = device

    def get_score(self, track, clip_id=0):
        track.rand = random.randint(0,10**8)

        video = self.load_frames_for_avasd(track)
        audio = self.load_audio_for_avasd(track)
        if Config.debug_mode:
            self.write_out(video, track.scene.get_audio(), track.scene.fps, track, clip_id)
        score = self.eval_model(video, audio, track.scene.fps)
        return score
    
    def write_out(self, video, audio,fps, track, clip_id):
        os.makedirs(f"./debug/talknet-inputs/{clip_id}/{track.scene.idx}", exist_ok=True)
        out_video = f"./debug/talknet-inputs/{clip_id}/{track.scene.idx}/video.mp4"
        Helper.write_video(video, "./debug/scene-track.tmp.mp4",fps=fps)
        new_video=mp.VideoFileClip("./debug/scene-track.tmp.mp4")
        new_video.audio = audio
        new_video.write_videofile(out_video, codec="libx264", audio_codec="aac",logger=None)
        os.remove("./debug/scene-track.tmp.mp4")

    def eval_model(self, video, audio, fps):
        self.model.eval()
        durationSet = {1,2,3,4,5,6}
        allScore = [] # Evaluation use TalkNet
        fps = round(fps)
        audio_scale = round(1/self.winstep)
        av_scale = audio_scale/fps
        #total duration of clip
        length = video.shape[0]
        audio = audio[:int(length * av_scale)]

        for duration in durationSet:
            duration = duration * fps 
            batchSize = int(math.ceil(length/duration))

            scores = []
            with torch.no_grad():
                end = None
                for i in range(batchSize + 1):
                    inputV = torch.FloatTensor(video[i*duration : (i+1) * duration,:,:]).unsqueeze(0).to(self.device)
                    
                    audio_dur = round(inputV.shape[1]/fps * audio_scale)
                    if end is None:
                        start = 0
                    else:
                        start = end
                    end = start + audio_dur
                    
                    inputA = torch.FloatTensor(audio[start:end,:]).unsqueeze(0).to(self.device)
                    padding_v_dims = 0

                    # padding_v_dims = max(0, int(math.ceil(inputA.shape[1]/4) - inputV.shape[1]))
                    # padding = torch.zeros((1,padding_v_dims, inputV.shape[2], inputV.shape[3])).to(self.device)
                    # inputV = torch.cat((inputV, padding),dim=1)
                    # padding_a_dims = max(0, int(inputV.shape[1]*av_scale) - inputA.shape[1])
                    # padding = torch.zeros((1, padding_a_dims, inputA.shape[2])).to(self.device)
                    # inputA = torch.cat((inputA, padding), dim=1)
                    # print(inputA.shape, inputV.shape)
                    if (inputA.shape[1] == 0 and inputV.shape[1] == 0):
                        break

                    embedA = self.model.model.forward_audio_frontend(inputA)
                    embedV = self.model.model.forward_visual_frontend(inputV)	
                    
                    embedA, embedV = self.model.model.forward_cross_attention(embedA, embedV)
                    out = self.model.model.forward_audio_visual_backend(embedA, embedV)
                    score = self.model.lossAV.forward(out, labels = None)
                    score = score[:score.shape[0]-padding_v_dims]
                    scores.append(score)
            scores = np.concatenate([arr for arr in scores])
            # print(scores.shape)
            allScore.append(scores)
        allScore = np.round((np.mean(np.array(allScore), axis = 0)), 1).astype(float)
        # print(allScore)
        return allScore
    
    def load_audio_for_avasd(self, track):

        #vibe coded with gpt and it doesn't fucking work 🙄
        start = track.frames[0].idx/track.scene.fps
        end = (track.frames[-1].idx + 1)/track.scene.fps

        command = ("ffmpeg -y -i %s -async 1 -ac 1 -vn -acodec pcm_s16le -ar 16000 -threads %d -ss %.3f -to %.3f %s -loglevel panic" % \
		      (track.scene.video_file, 2, start, end, "./.cache/scene-audio.wav"))
        output = subprocess.call(command, shell=True, stdout=None)
        sample_rate, audio = wavfile.read( "./.cache/scene-audio.wav")
        return mfcc(audio, 16000, numcep = 13, winlen = 0.025, winstep = 0.010)



        # audio = track.scene.get_audio(start,end)
        # # # Extract the audio as a NumPy array at 16000 Hz (matching the expected sample rate).
        # # audio = audio.to_soundarray(fps=track.scene.fps)
        # audio.write_audiofile("./.cache/tmp_output.wav")
        # sample_rate, audio = wavfile.read("./.cache/tmp_output.wav")
        # if audio.ndim == 2:
        #     # Convert to mono by averaging the two channels
        #     audio = np.mean(audio, axis=1)
        # audioFeature = mfcc(audio, sample_rate, numcep = 13,nfft=4096, winlen = 0.025, winstep = 0.010)
        # print(audioFeature.shape)
        # return audioFeature
    
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
            frame.set_bbox(bbox)
            
            # print(bbox)
            # try:    
               
            # frame.cv2 = frame.crop_cv2()
                
            bsi = int(bs * (1 + 2 * cs))
            frame.cv2 = np.pad(frame.cv2, ((bsi,bsi), (bsi,bsi), (0, 0)), 'constant', constant_values=(110, 110))
            my = y + bsi 
            mx = x + bsi

            ys = max(int(my-bs),0)
            ye = min(int(my+bs*(1+2*cs)), frame.cv2.shape[0])
            xs = max(int(mx-bs*(1+cs)),0)
            xe = min(int(mx+bs*(1+cs)),frame.cv2.shape[1])
            if xs == xe:
                if xe == 0:
                    xe = 1 
                if xs == frame.cv2.shape[1]:
                    xs = frame.cv2.shape[1] - 1
            if ys == ye:
                if ys == frame.cv2.shape[0]:
                    ys = frame.cv2.shape[0]  -1 
                if ye == 0:
                    ye = 1
            frame.cv2 = frame.cv2[ys:ye, xs:xe]
            # print("frame")
            # print(frame.bbox)
            # print(int(my-bs),int(my+bs*(1+2*cs)),int(mx-bs*(1+cs)),int(mx+bs*(1+cs)))
            # print(frame.cv2.shape)
            frame.cv2 = cv2.resize(frame.cv2, (224, 224))
            frame.cv2 = cv2.cvtColor(frame.cv2, cv2.COLOR_BGR2GRAY)
            frame.cv2 = cv2.resize(frame.cv2, (224,224))
            # print(frame.cv2.shape)
            
            #idk why he only uses half the resized frame?
            #probably for efficiency
            #need to read paper
            frame.cv2 = frame.cv2[int(112-(112/2)):int(112+(112/2)), int(112-(112/2)):int(112+(112/2))]
            #resize in case crop messed it up
            # frame.cv2 = frame.cv2.resize(frame.cv2, (112,112))
            
            # if Logger.debug:
            #     os.makedirs(f"./.cache/talknet-inputs/{track.scene.idx}/{track.rand}", exist_ok=True)
            #     cv2.imwrite(f"./.cache/talknet-inputs/{track.scene.idx}/{track.rand}/{frame.idx}.jpg", frame.cv2)
            # except Exception as e:
            #     print(e)
            #     pass
        # exit()

        return np.array([frame.cv2 for frame in track.frames])