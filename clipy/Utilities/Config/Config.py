#TODO implement a professional config file that gets loaded in main 
import torch 

class Config():

    args = None
    
    def init(args):
        Config.args = args
        Config.debug_mode = args.debug
        Config.device = args.device
        Config.use_profiler = args.use_profiler
        
        if Config.debug_mode:
            print("Warning: Debug Mode Set To True")
        
