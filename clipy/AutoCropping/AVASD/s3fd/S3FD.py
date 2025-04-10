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


class S3FDImageSet(Dataset):

    def __init__(self, scenes):

        self.scenes = scenes
        self.current_scene = 0
        self.counter = 0
        self.frames = []
        self.w = None 
        self.h = None
        self.load_frames_from_disk()
        
    
    def __len__(self):
        l = 0
        for scene in self.scenes:
            l += scene.frame_duration
        return l
    
    def load_frames_from_disk(self):
        for scene in self.scenes:
            for frame in scene.get_frames():
                if self.w is None or self.h is None:
                    self.w = frame.shape[1]
                    self.h = frame.shape[0]
                self.frames.append(frame)

    def __getitem__(self, idx):
        return self.scale_image(self.frames[idx])
    
    def scale_image(self, frame):
        scaled_img = cv2.resize(frame, dsize=(0, 0), fx=1, fy=1, interpolation=cv2.INTER_LINEAR)
        scaled_img = np.swapaxes(scaled_img, 1, 2)
        scaled_img = np.swapaxes(scaled_img, 1, 0)
        scaled_img = scaled_img[[2, 1, 0], :, :]
        scaled_img = scaled_img.astype('float32')
        scaled_img -= img_mean
        scaled_img = scaled_img[[2, 1, 0], :, :]
        return torch.from_numpy(scaled_img)


    
class S3FD():

    def __init__(self, device='cuda'):

        tstamp = time.time()
        self.device = device

        # print('[S3FD] loading with', self.device)
        self.net = S3FDNet(device=self.device).to(self.device)
        PATH = os.path.join(os.getcwd(), PATH_WEIGHT)
        if not os.path.exists(PATH_WEIGHT):
            Logger.log("Downloading S3FD Model Weights")
            Helper.download_cf("sfd_face.pth", PATH_WEIGHT)
        state_dict = torch.load(PATH, map_location=self.device)
        self.net.load_state_dict(state_dict)
        self.net.eval()
        # print('[S3FD] finished loading (%.4f sec)' % (time.time() - tstamp))
    
    def detect_faces(self, scenes, conf_th=0.8, scales=[1]):

        # all frames from input video shoiuld be the same size
        self.conf_th = conf_th

        dataset = S3FDImageSet(scenes)
        self.w = dataset.w 
        self.h = dataset.h
        loader = DataLoader(dataset, batch_size=32,num_workers=4, shuffle=False)
        bboxes = []
        with torch.no_grad():
            for x in tqdm(loader, total=len(loader)):
                
                x = x.to(self.device)
                y = self.net(x)
                bboxes.extend(self.get_bboxes_from_detections(y.data))

        return bboxes
    
    def get_bboxes_from_detections(self, outputs):
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
            ret.append(bboxes)
        return ret
