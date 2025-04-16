import cv2
import math 
import numpy as np 

class Arg():
    
    def __init__(self, name, default=None, required=True):
        self.name = name 
        self.default = default 
        self.required = True

class FrameOp():


    
    arg_format = []
    
    def __init__(self, *args, **kwargs):
        #initialize args in inherited class
        self.process_args(self, args, kwargs)
    
    def __call__(self, frame):

        return self.process_frame(frame)
   
    def process_frame(self, frame):
        #TODO
        #to be implemented by inherited class
        pass

    @classmethod
    def process_args(cls,self, args, kwargs):
        for i, arg in enumerate(cls.arg_format):
            if i < len(args):
                setattr(self, arg.name, args[i])
                continue 
               
            if arg.name in kwargs.keys():
                setattr(self, arg.name, kwargs[arg.name])
                continue 

            raise Exception("FrameOp Arguments Not Formatted Properly")
            


class CropOp(FrameOp):
    
    arg_format = [Arg("xs"), Arg("xe"), Arg("ys"), Arg("ye")]

    def process_frame(self, frame):
        if self.ys is None:
            self.ys = 0 
        if self.xs is None:
            self.xs = 0 
        if self.xe is None:
            self.xe = frame.shape[1]
        if self.ye is None:
            self.ye = frame.shape[0]
        return frame[self.ys:self.ye, self.xs:self.xe]

class ResizeOp(FrameOp):

    arg_format = [Arg("width"), Arg("height")]

    def process_frame(self, frame):
        return cv2.resize(frame, (self.width, self.height))
    
class ResizeInWindowOp(FrameOp):

    arg_format = [Arg("new_width"), Arg("new_height")]

    def process_frame(self, frame):
        new_w = self.new_width 
        new_h = int(self.new_width * (frame.shape[0]/frame.shape[1]))

        #resizes old frame to be new width and height to fit inside 
        #short video whilst maintaining the same aspect ratio
        frame = cv2.resize(frame, (int(new_w), int(new_h)))
        
        #make it work for b&w video
        #makes the new frame entirely black
        if len(frame.shape) == 3:
            new_f = np.zeros((self.new_height, self.new_width, 3))
        else:
            new_f = np.zeros((self.new_height, self.new_width))
        
        #adds old frame inside of new frame and returns it

        ys = int(new_f.shape[0]/2) - math.floor(frame.shape[0]/2)
        ye = ys + frame.shape[0]
        new_f[ys:ye] = frame 
        return new_f.astype(np.uint8)