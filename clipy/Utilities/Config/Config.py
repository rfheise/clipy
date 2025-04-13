#TODO implement a professional config file that gets loaded in main 
import torch 
import argparse

class Config():

    args = None
    
    def init(debug=False):

        Config.args = Config.init_args()
        Config.debug_mode = Config.args.debug_mode
        if Config.debug_mode:
            Config.init_debug()
        Config.device = Config.args.device
        Config.use_profiler = Config.args.use_profiler
    
    def init_args():

        default_device = "cuda" if torch.cuda.is_available() else "cpu"

        parser = argparse.ArgumentParser(description = "Clipy: A video processing tool")
        parser.add_argument('--debug-mode', dest='debug_mode',default=False, action='store_true', help='Debug mode')
        parser.add_argument('-i', '--input', type=str,required=True, help='Input video path')
        parser.add_argument('-o', '--output', type=str,required=True, help='Output directory')
        parser.add_argument('--subtitle-model', type=str, default="turbo", help='Subtitle model to use')
        parser.add_argument('--gpt-highlighting-model', type=str, default="gpt-4o", help='GPT model to use for highlighting')
        parser.add_argument('--scale-s3fd', type=float, default=0.25, help='Scale factor for resizing SF3D Input') 
        parser.add_argument('--min-face-percentage', type=float, default=2, help='Minimum face percentage for detection')
        parser.add_argument('--cache-level', type=str, default="basic", help='Cache level to use')  
        parser.add_argument('--num-failed-det', type=int, default=10, help='Number of failed detections before face is rejected')
        parser.add_argument('--min-frames-in-track', type=int, default=20, help='Minimum frames in track for detection')  
        parser.add_argument('--device', type=str, default=default_device, help='Device to use for processing (e.g., "cuda", "cpu")')  
        parser.add_argument('--use-profiler',default=False, action='store_true', help='Use profiler for performance measurement')
        parser.add_argument('--cache-dir', type=str, default="./.cache", help='Directory to store cache files')
        parser.add_argument('--cache-file', type=str, default=None, help='Cache file name')
        parser.add_argument('--conf-th-s3fd', type=float, default=0.5, help='Confidence threshold for face detection')
        parser.add_argument('--load-cache-file', type=str, default=None, help='Cache file to load')
        parser.add_argument('--no-preprocess-video', default=False, action='store_true', help='Do not preprocess video before running clipy')
        args = parser.parse_args()
        return args
        
    def init_debug():

        Config.args.debug_mode = True
        Config.args.load_cache_file = 'fd_test.sav'
        Config.args.gpt_highlighting_model = "gpt-4o-mini"
        Config.args.subtitle_model = "tiny.en"
        Config.args.cache_level = "dev"
        Config.args.cache_file = "fd_test.sav"

