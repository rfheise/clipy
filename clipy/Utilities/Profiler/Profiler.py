import time
from ..Config.Config import Config
from ..Logging.Logger import Logger
from collections import defaultdict

"""
Profiler.py is used to time various parts of the code using wall clock time
I could probably implement a better profiler but using wall clock time isn't terrible
It helps identify bottlenecks and determine what section of the code needs optimized
"""

class Profile():

    """
    A profile is a single item that gets timed
    i.e. the cropping pipeline
    """

    def __init__(self, name):
        self.name = name
        self.start_time = None
        self.elapsed_time = None
    
    def start(self):
        #starts the profiler
        self.start_time = time.time()
    
    def stop(self):
        #stops the profiler

        #a single profile can be called
        #multiple times
        #if that is the case add to the total time rather than restart
        if self.elapsed_time is None:
            self.elapsed_time = 0
        self.elapsed_time += time.time() - self.start_time
        self.start_time = None 
    
    def summary(self):
        #if elapsed time is not set that means the profile wasn't stopped
        if self.elapsed_time is None:
            Logger.log_warning(f"Profile {self.name} not stopped properly")
            return 
        
        minutes = int(self.elapsed_time//60)
        seconds = int(self.elapsed_time % 60)

        #logs runtime data
        Logger.new_line()
        Logger.log(f"Profile {self.name} took {minutes}:{seconds:02d} minutes")
        Logger.new_line()

class Profiler():
    
    #the profiler is a global object that 
    #manages all profiles across the codebase 

    profiles = {}

    def init():
        pass
        

    def start(name=None):
        #initializes a profile

        #if use profiler is not set don't use it and ignore call
        if not Config.use_profiler:
            return
        
        #initialize total if total is not set
        if name is None:
            name = "total"
        
        #initialize profile and add it to global profiles
        if name not in Profiler.profiles.keys():
            Profiler.profiles[name] = Profile(name)
        Profiler.profiles[name].start()
    
    def stop(name=None):
        #stops timing a profile 

        #if use profiler is not set don't use it and ignore call
        if not Config.use_profiler:
            return
        
        #if stop doesn't have an argument that 
        #means it's the final call and all profiles
        #are ready to be summarized
        summary = False 
        if name is None:
            summary = True 
            name = "total"
        
        if name not in Profiler.profiles:
            Logger.log_warning(f"Profile {name} not started")
            return

        #stops timing profile
        Profiler.profiles[name].stop()

        #if final call
        #summarize profiles
        if summary:
            for profile in Profiler.profiles.values():
                profile.summary()
        
        