import time
from ..Config.Config import Config
from ..Logging.Logger import Logger
from collections import defaultdict

class Profile():

    def __init__(self, name):
        self.name = name
        self.start_time = None
        self.elapsed_time = None
    
    def start(self):
        self.start_time = time.time()
    
    def stop(self):
        if self.elapsed_time is None:
            self.elapsed_time = 0
        self.elapsed_time += time.time() - self.start_time
        self.start_time = None 
    
    def summary(self):
        if self.elapsed_time is None:
            Logger.log_warning(f"Profile {self.name} not stopped properly")
            return 
        minutes = int(self.elapsed_time//60)
        seconds = int(self.elapsed_time % 60)
        Logger.new_line()
        Logger.log(f"Profile {self.name} took {minutes}:{seconds:02d} minutes")
        Logger.new_line()

class Profiler():
    
    profiles = {}

    def init():
        pass
        

    def start(name=None):
        if not Config.use_profiler:
            return
        if name is None:
            name = "total"
        if name not in Profiler.profiles.keys():
            Profiler.profiles[name] = Profile(name)
        Profiler.profiles[name].start()
    
    def stop(name=None):
        if not Config.use_profiler:
            return
        summary = False 
        if name is None:
            summary = True 
            name = "total"
        
        if name not in Profiler.profiles:
            Logger.log_warning(f"Profile {name} not started")
            return

        Profiler.profiles[name].stop()

        if summary:
            for profile in Profiler.profiles.values():
                profile.summary()
        
        