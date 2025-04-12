from .ContentHighlighting import ChatGPTHighlighter
from .AutoCropping import AVASD
from .Pizzazz import VideoProcessor, SubtitleCreator, ResizeCreator
from .Utilities import Logger, Cache, Timestamp, Profiler, Config
import sys
import os
import argparse 
import torch 

def main():

    default_device = "cuda" if torch.cuda.is_available() else "cpu"

    parser = argparse.ArgumentParser(description = "Clipy: A video processing tool")
    parser.add_argument('--debug-mode', dest='debug_mode',default=False, action='store_true', help='Debug mode')
    parser.add_argument('-i', '--input', type=str,required=True, help='Input video path')
    parser.add_argument('-o', '--output', type=str,required=True, help='Output directory')
    parser.add_argument('--subtitle-model', type=str, default="turbo", help='Subtitle model to use')
    parser.add_argument('--gpt-highlighting-model', type=str, default="gpt-4o", help='GPT model to use for highlighting')
    parser.add_argument('--scale-sf3d', type=float, default=0.25, help='Scale factor for resizing SF3D Input') 
    parser.add_argument('--min-face-percentage', type=float, default=2, help='Minimum face percentage for detection')
    parser.add_argument('--cache-level', type=str, default="basic", help='Cache level to use')  
    parser.add_argument('--num-failed-det', type=int, default=10, help='Number of failed detections before face is rejected')
    parser.add_argument('--min-frames-in-track', type=int, default=20, help='Minimum frames in track for detection')  
    parser.add_argument('--device', type=str, default=default_device, help='Device to use for processing (e.g., "cuda", "cpu")')  
    parser.add_argument('--use-profiler',default=False, action='store_true', help='Use profiler for performance measurement')
    
    args = parser.parse_args()
    Config.init(args)

    if len(sys.argv) != 3:
        Logger.log_error("Usage: python main.py <video_path> <output_dir>")
        sys.exit(1)
    

    fname = Config.args.input
    out_dir = Config.args.output
    # platform = sys.argv[3]

    Profiler.start()

    video_path = fname
    cache = Cache(level=Config.args.cache_level)
    os.makedirs("./.cache", exist_ok=True)
    cache_file = "./.cache/fd_test.sav"
    cache.set_save_file(cache_file)
    # cache.load(cache_file)
    # cache.clear("scenes")


    # Highlighting the subtitles
    highlighter = ChatGPTHighlighter(video_path,model="gpt-4o", cache=cache, sub_model="turbo")
    intervals = highlighter.highlight_intervals()
    # intervals.insert(0,Timestamp(1498,1546))
    cache.save(cache_file)

    # Cropping the video
    # cache.clear("videos")
    # for i in range(30):
    #     cache.clear(f"clip-{i}-scenes")
    cropper = AVASD(video_path, intervals, cache=cache)
    clips = cropper.crop()
    cache.save(cache_file)

    # # Adding pizzazz to the subtitles
    creator = VideoProcessor(clips, cache = cache)

    if not Logger.debug_mode:

        creator.add_pizzazz(ResizeCreator(new_size=(1080,1920),cache=cache))

    creator.add_pizzazz(SubtitleCreator(cache=cache))
    creator.render(output_dir=out_dir)
    # cache.save(cache_file)

    Profiler.stop()
    

if __name__ == "__main__":
    main()
