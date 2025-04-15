import pickle 
import os 
from ..Logging.Logger import Logger
from ..Profiler.Profiler import Profiler

"""
This module is used to create a cache. Caches are used extensively throughout the project for two main purposes

1. Caching Utilities That Are Needed By Various Parts of the pipeline (i.e. scenes)
2. Caching parts of the pipeline so that while developing you can pick up right where you left off without rerunning the prior steps of the pipeline 

Right now the Cache just pickles all objects in the cache but could be more "professional"

The GhostCache is used as a default Cache when a regular Cache isn't specified.
This allows me to reuse the logic without having to do 
if cache is not None:
    do X
else:
    do Y 

Instead I can just do 
if cache.exists("item"):
    item = cache.load_item("item")
    return item
item = processing logic for item 
cache.save("item", item, cache level for item)

In my opinion this makes the code cleaner as cache.exists always returns false in ghost cache

The Cache Level is the level for which the cache will be used. 
There are 3 cache levels basic, dev, and debug
Each cache level also uses the previous cache levels below it. 
i.e. dev also uses the basic cache and the debug cache uses all caches 

Each level is used as follows

Basic - always used (subtitles, py scene, etc...)
Dev - used to pick up from where you left off (if working on AVASD will automatically load highlighter)
Debug - used for debugging various parts of code

"""
class Cache():

    cache_levels = ["basic", "dev", "debug"]

    def __init__(self, level="basic", *args, **kwargs):
        # initializes the cache to use all level less than or equal to the specified level 
        # i.e. debug uses the dev and basic cache as well
        # dev just uses dev and basic
        # basic just uses itsefl 

        if level not in Cache.cache_levels:
            Logger.log_error(f"Cache Level {level} not in {Cache.cache_levels}")
            exit(1)

        for lvl in Cache.cache_levels:
            setattr(self, lvl, False)

        idx = Cache.cache_levels.index(level)
        for i in range(idx + 1):
            setattr(self, Cache.cache_levels[i], True)
        
        self.init_cache()
        self.save_file = None
        
    def get_item(self, key):

        if self.cache is None:
            return None
        
        return self.cache.get(key)

    def set_item(self, key, val, level='basic'):
        #updates cache with key:value at specified level
        if not getattr(self, level) or self.cache is None:
            return
        self.cache[key] = val
        
    def exists(self, key):
        #returns whether key is set in cache
        return self.cache is not None and key in self.cache and self.cache[key] is not None
    
    def init_cache(self):
        #initializes the cache
        if self.basic:
            self.cache = {}
        else:
            self.cache = None

    def load(self, fname=None):
        #loads the cache from the speficied filename
        Profiler.start("caching")
        if self.save_file is not None:
            fname = self.save_file
        Logger.debug("Loading Cache")
        #should work for now but need to improve later 
        if fname is None or not os.path.exists(fname):
            Logger.log_warning("Cache File Does Not Exist Skipping Initialization")
            return 
        
        with open(fname, 'rb') as f:
            self.cache = pickle.load(f)
        
        if self.cache is None:
            Logger.log_warning("Cache set to None after load")
        Profiler.stop("caching")
        
    def save(self, fname=None):
        #saves the cache at the specified file name
        #right now it just pickles everything but I intend to make a more professional cache later on
        if self.save_file is None:
            Logger.debug("Cache file not set skipping save")
            return
        Profiler.start("caching")
        fname = self.save_file
        if fname is None:
            Logger.log_warning("Cache File Not Specified")
            return
        Logger.debug("Saving Cache")
        with open(fname, 'wb') as f:
            pickle.dump(self.cache, f)
        Profiler.stop("caching")
    
    def clear(self, key = None):
        #empties cache if no key is specified
        if key is None:
            self.init_cache()
        else:
            #otherwise it just empties value at key
            self.set_item(key, None)

    def set_save_file(self, fname):
        #sets default save file
        self.save_file = fname

#read above for explanation of GhostCache
class GhostCache(Cache):

    def __init__(self):
        pass 

    def get_item(self, key):
        return None 
    
    def set_item(self, key, val):
        pass 

    def exists(self, key):
        return False
    
    def load(self, fname):
        Logger.log_warning("Loading Ghost Cache")

    def save(self, fname):
        Logger.log_warning("Saving Ghost Cache")
        pass