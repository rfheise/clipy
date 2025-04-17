
import torch 
import argparse


"""
TODO implement a professional config file that gets loaded in main 

Config.py 

This module specifies all of the default parameters that can be configured by the user when running the program.
It also parses all of the arguments passed in by the user and saves them to the global config object.
The global config object is then used by pretty much everything to load the default config values.

"""

    
    

class Preset():

    ffmpeg_crf = 23
    ffmpeg_preset = "medium"
    output_res = 720
    subtitle_model = "turbo"
    gpt_highlighting_model = 'o4-mini'
    name = "default preset"

class Good(Preset):

    name = "good"

class VeryGood(Preset):

    name = "verygood"
    ffmpeg_crf = 18 
    output_res = 1080
    subtitle_model = "turbo"
    gpt_highlighting_model = 'o4-mini'
    ffmpeg_preset = 'slow'

class Mid(Preset):

    name = "mid"
    ffmpeg_crf = 23 
    output_res = 480
    subtitle_model = "tiny.en"
    gpt_highlighting_model = 'o4-mini'
    ffmpeg_preset = 'medium'

class Bad(Preset):

    name = "bad"
    ffmpeg_crf = 28 
    output_res = 480
    subtitle_model = "small.en"
    gpt_highlighting_model = 'gpt-4o-mini'
    ffmpeg_preset = 'medium'

class VeryBad(Preset):

    name = "verybad"
    ffmpeg_crf = 35 
    output_res = 360
    subtitle_model = "tiny.en"
    gpt_highlighting_model = 'gpt-4o-mini'
    ffmpeg_preset = 'veryfast'

presets = [VeryBad, Bad, Mid, Good, VeryGood]

class Config():

    args = None
    
    def init(debug=False):

        #initializes all the arguments specified by the user
        Config.args = Config.init_args()
        if debug:
            Config.args.debug_mode = debug

        Config.debug_mode = Config.args.debug_mode
        if Config.debug_mode:
            Config.init_debug()

        Config.init_preset(Config.args.preset)
        
        
        
        #sets device to be used by torch models
        Config.device = Config.args.device

        #sets whether or not the profiler should be used to time the pipeline
        Config.use_profiler = Config.args.use_profiler
    
    def init_args():

        #wall of arguments that specify what each one does
        
        default_device = "cuda" if torch.cuda.is_available() else "cpu"

        parser = argparse.ArgumentParser(description = "Clipy: A video processing tool")
        parser.add_argument('--debug-mode', dest='debug_mode',default=False, action='store_true', help='Debug mode')
        parser.add_argument('-i', '--input', type=str,required=True, help='Input video path')
        parser.add_argument('-o', '--output', type=str,required=True, help='Output directory')
        parser.add_argument('--subtitle-model', type=str, default="turbo", help='Subtitle model to use')
        parser.add_argument('--gpt-highlighting-model', type=str, default="o4-mini", help='GPT model to use for highlighting')
        parser.add_argument('--scale-s3fd', type=float, default=0.25, help='Scale factor for resizing SF3D Input') 
        parser.add_argument('--min-face-percentage', type=float, default=0, help='Minimum face percentage for detection')
        parser.add_argument('--cache-level', type=str, default="basic", help='Cache level to use')  
        parser.add_argument('--num-failed-det', type=int, default=10, help='Number of failed detections before face is rejected')
        parser.add_argument('--min-frames-in-track', type=int, default=20, help='Minimum frames in track for detection')  
        parser.add_argument('--device', type=str, default=default_device, help='Device to use for processing (e.g., "cuda", "cpu")')  
        parser.add_argument('--use-profiler',default=False, action='store_true', help='Use profiler for performance measurement')
        parser.add_argument('--cache-dir', type=str, default="./.cache", help='Directory to store cache files')
        parser.add_argument('--cache-file', type=str, default=None, help='Cache file name')
        parser.add_argument('--conf-th-s3fd', type=float, default=0.5, help='Confidence threshold for face detection')
        parser.add_argument('--num-clips', type=int, default=None, help='Number of clips to output')
        parser.add_argument('--load-cache-file', type=str, default=None, help='Cache file to load')
        parser.add_argument('--no-preprocess-video', default=False, action='store_true', help='Do not preprocess video before running clipy')
        parser.add_argument('--max-frame-buffer-size', type=int, default = 25, help='maximum size (in frames) of frame buffer')
        parser.add_argument('--save-bboxes', default=False, action='store_true', help="Create bounding box video for each clip" )
        parser.add_argument('--save-facial-tracks', default=False, action='store_true', help="Save video of each facial track")
        parser.add_argument('--output-res', type=int, default=1080, help="output video resolution")
        parser.add_argument('--ffmpeg-preset', type=str, default='medium', help="ffmpeg preset")
        parser.add_argument('--ffmpeg-crf', type=int, default=18, help="quality control for ffmpeg")
        parser.add_argument('--preset', type=str, default="good", help="quality control for clipy")
        parser.add_argument('--render_pipeline', action='store_true', default=False, help="render as pipeline or sequentially")
        args = parser.parse_args()

        return args
        
    def init_debug():

        #debug mode is just a shorthand for specifying several arguments
        Config.args.debug_mode = True
        Config.args.load_cache_file = 'fd_test.sav'
        Config.args.gpt_highlighting_model = "gpt-4o-mini"
        Config.args.subtitle_model = "tiny.en"
        Config.args.cache_level = "dev"
        Config.args.cache_file = "fd_test.sav"
        Config.args.save_facial_tracks = False 
        Config.args.save_bboxes = False
        Config.args.preset = "bad"
        Config.args.use_profiler = True

    def init_preset(preset):
        
        if preset not in [pset.name for pset in presets]:
            print(f"preset {preset} does not exist")

        for pset in presets:
            if preset == pset.name:
                preset = pset
                break

        Config.args.ffmpeg_crf = preset.ffmpeg_crf 
        Config.args.ffmpeg_preset = preset.ffmpeg_preset
        Config.args.output_res = preset.output_res 
        Config.args.subtitle_model = preset.subtitle_model
        Config.args.gpt_highlighting_model = preset.gpt_highlighting_model 
