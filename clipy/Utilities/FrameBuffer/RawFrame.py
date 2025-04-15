
#implement raw frame first 
#add global buffer if needed
import os 
from ..Logging.Logger import Logger 
from ..Profiler.Profiler import Profiler
from ..Config.Config import Config
import cv2 

class FrameBuffer():

    def __init__(self, frame_dir=None, max_buffer_len=None):

        if max_buffer_len is None:
            max_buffer_len = Config.args.max_frame_buffer_size

        #RawFrame objects
        self.frames = {}
        self.frame_ids = set()
        
        #Loaded Frames
        self.buffer_ids = []
        self.buffer = {}

        self.max_buffer_len = max_buffer_len

        if not frame_dir:
            self.frame_dir = os.path.join(".cache","frames")
        else:
            self.frame_dir = frame_dir 
            
        os.makedirs(self.frame_dir, exist_ok=True)

    def add_frame(self, frame_idx, frame_cv2):
        if frame_idx in self.frame_ids:
            Logger.log_warning("adding existing frame to buffer")
            return self.frames[frame_idx]
        frame = RawFrame(frame_idx, frame_cv2, os.path.join(self.frame_dir, f"f{frame_idx}.jpg"),buffer=self, dirty=True)
        self.frames[frame_idx] = frame
        self.frame_ids.add(frame_idx)
        self.add_frame_to_buffer(frame)

        return frame
    
    def add_frame_to_buffer(self, raw_frame):
        if raw_frame.idx not in self.frame_ids:
            Logger.log_error("Added Freed Frame to Buffer")
            exit(1)
        if raw_frame.idx in self.buffer_ids:
            return
        if len(self.buffer_ids) >= self.max_buffer_len:
            self.remove_top()
        self.buffer_ids.append(raw_frame.idx)
        self.buffer[raw_frame.idx] = raw_frame


    def get_frame(self, idx):

        if idx not in self.frame_ids:
            Logger.log_warning("frame not in buffer")
            return None
        
        return self.frames[idx]
    
    def remove_top(self):

        top_id = self.buffer_ids[0]
        del self.buffer_ids[0]
        self.buffer[top_id].to_disk()
        del self.buffer[top_id]
    
    def remove(self, idx):
        #shouldn't double free
        #remove this in the future and fix data flow
        
        if idx not in self.frame_ids:
            return
        self.frame_ids.remove(idx)
        frame = self.frames[idx]
        if idx in self.buffer_ids:
            del self.buffer[idx]
            self.buffer_ids.remove(idx)
        frame.remove_from_disk()
        del self.frames[idx]
    
    def clear(self, frame_ids=None):

        Logger.debug("Buffer 💣")
        if frame_ids is None:
            frame_ids = [*self.frame_ids]

        for idx in frame_ids:
            self.remove(idx)
    
    def flush(self):

        while len(self.buffer_ids) > 0:
            self.remove_top()



class RawFrame():

    def __init__(self, idx, cv2, fname, dirty, buffer=None):
        self.cv2 = cv2
        self.idx = idx
        self.dirty = dirty=dirty
        self.buffer = buffer 
        self.fname = fname
        self.render_ops = []
    
    def to_disk(self):
        Profiler.start("frame saving")
        if not self.dirty:
            self.cv2 = None
            return
        success = cv2.imwrite(self.fname, self.cv2)
        if not success:
            Logger.log_error("Error writing frame to disk")
            exit(5)
        self.cv2 = None 
        self.dirty = False
        Profiler.stop("frame saving")
    
    def set_cv2(self,cv2):

        self.cv2 = cv2

        self.dirty = True 
        if self.buffer:
            self.buffer.add_frame_to_buffer(self)
        

    def get_cv2(self):

        if self.cv2 is not None:
            return self.cv2
        
        Profiler.start("frame loading")
        self.dirty = False
        self.cv2 = cv2.imread(self.fname)

        if self.cv2 is None:
            Logger.log_error("Error reading frame from disk")
            exit(7)

        if self.buffer:
            self.buffer.add_frame_to_buffer(self)
        Profiler.stop("frame loading")
        return self.cv2
    
    def clear(self):
        self.buffer.remove(self.idx)

    def remove_from_disk(self):
        
        if os.path.exists(self.fname):
            os.remove(self.fname)

    def add_op(self, op):
        
        self.render_ops.append(op)
    
    def render(self):
        
        #careful because cv2 no longer 
        #managed by buffer
        raw_frame_cv2 = self.cv2
        if not self.cv2 is not None:
            raw_frame_cv2 = cv2.imread(self.fname)
            if raw_frame_cv2 is None:
                Logger.log_error("Error reading frame from disk")
                exit(7)
        for op in self.render_ops:
            raw_frame_cv2 = op(raw_frame_cv2)
        return raw_frame_cv2