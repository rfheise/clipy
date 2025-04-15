import time, os, sys, subprocess
import numpy as np
import cv2
import torch
from torchvision import transforms
from .nets import S3FDNet
from .box_utils import nms_
from ....Utilities import Helper, Logger, Profiler
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm 

PATH_WEIGHT = os.path.join(os.path.dirname(__file__), "sfd_face.pth")
# if os.path.isfile(PATH_WEIGHT) == False:
#     Link = "1KafnHz7ccT-3IyddBsL5yi2xGtxAKypt"
#     cmd = "gdown --id %s -O %s"%(Link, PATH_WEIGHT)
#     subprocess.call(cmd, shell=True, stdout=None)
img_mean = np.array([104., 117., 123.])[:, np.newaxis, np.newaxis].astype('float32')

"""
Code for running S3FD face detector on a set of images. This is the only code I modified from TalkNet's implementation of S3FD.
I made it work with my custom classes and made it so it uses batched inference.

"""

class S3FDImageSet(Dataset):

    def __init__(self, clip, scale):

        # data loader for Scene[] input
        self.clip = clip 
        self.scale = scale
        self.current_scene = 0
        self.counter = 0
        self.frames = []
        self.w = None 
        self.h = None
        self.load_frames_from_disk()
        
    
    def __len__(self):

        # returns length of the clip in frames
        return self.clip.get_end_frame() - self.clip.get_start_frame()
    
    def load_frames_from_disk(self):

        # loads all frames from disk and sets init width and height
        # assumes all width and heights are constant throughout the video
        for frame in self.clip.get_frames():
            if self.w is None or self.h is None:
                self.w = frame.get_cv2().shape[1]
                self.h = frame.get_cv2().shape[0]
            self.frames.append(frame)

    def __getitem__(self, idx):
        return self.scale_image(self.frames[idx].get_cv2())
    
    def scale_image(self, frame):
        
        #scales the image to be self.scale% of the original size
        # this significantly speeds up inference time without diminishing accuracy by much
        scaled_img = cv2.resize(frame, dsize=(0, 0), fx=self.scale, fy=self.scale, interpolation=cv2.INTER_LINEAR)
        scaled_img = np.swapaxes(scaled_img, 1, 2)
        scaled_img = np.swapaxes(scaled_img, 1, 0)
        scaled_img = scaled_img[[2, 1, 0], :, :]
        scaled_img = scaled_img.astype('float32')
        scaled_img -= img_mean
        scaled_img = scaled_img[[2, 1, 0], :, :]

        return torch.from_numpy(scaled_img)


    
class S3FD():

    def __init__(self, device='cuda'):

        self.device = device

        self.net = S3FDNet(device=self.device).to(self.device)
        PATH = os.path.join(os.getcwd(), PATH_WEIGHT)

        # downloads pre-trained weights if they don't exist
        if not os.path.exists(PATH_WEIGHT):
            Logger.log("Downloading S3FD Model Weights")
            Helper.download_cf("sfd_face.pth", PATH_WEIGHT)
        state_dict = torch.load(PATH, map_location=self.device)
        self.net.load_state_dict(state_dict)
        self.net.eval()
    
    def detect_faces(self, clip, conf_th=0.5, scales=[.5],min_face_percentage=2):

        #confidence keep threshold
        self.conf_th = conf_th
        
        #scale doesn't need to be an array
        #keeping same implementation as og talknet for the ~ vibes ~
        self.scale = scales[0]
        dataset = S3FDImageSet(clip, self.scale)
        self.w = dataset.w 
        self.h = dataset.h
        
        # min face size to keep 
        # this is a percentage of the total image area
        self.min_face_size = round(min_face_percentage * self.w * self.h / 100)
        
        loader = DataLoader(dataset, batch_size=32,num_workers=0, shuffle=False)
        bboxes = []
        
        # runs inference on all frames in clip
        with torch.no_grad():
            for x in tqdm(loader, total=len(loader)):
                
                x = x.to(self.device)
                y = self.net(x)
                bboxes.extend(self.get_bboxes_from_detections(y.data))

        return bboxes
    
    def get_bboxes_from_detections(self, outputs):
        
        # iterates over the output of the model and returns bboxes that meet criteria 
        # rescales bboxes to be the same size as input image 
        
        ret = []
        for k in range(outputs.shape[0]):
            scale = torch.Tensor([self.w, self.h, self.w, self.h])
            detections = outputs[k].unsqueeze(0)
            bboxes = np.empty(shape=(0, 5))
            for i in range(detections.size(1)):
                j = 0
                while detections[0, i, j, 0] > self.conf_th:
                    score = detections[0, i, j, 0]
                    pt = (detections[0, i, j, 1:] * scale).cpu().numpy()
                    bbox = (pt[0], pt[1], pt[2], pt[3], score)
                    bboxes = np.vstack((bboxes, bbox))
                    j += 1

            keep = nms_(bboxes, 0.1)
            bboxes = bboxes[keep]
            keep = (bboxes[:, 3] - bboxes[:,1]) * (bboxes[:, 2] - bboxes[:,0]) > self.min_face_size
            bboxes = bboxes[keep]
            ret.append(bboxes)
        return ret
