from .ContentHighlighting import ChatGPTHighlighter
from .AutoCropping import AVASD
from .Pizzazz import VideoProcessor, SubtitleCreator, ResizeCreator
from .Utilities import Logger, Cache, Timestamp, Profiler, Config, Helper
import sys
import os

def main():

    #initializes the logger and processes input args
    Config.init()
    Logger.init()

    #gets in file & outdir from input args
    fname = Config.args.input
    out_dir = Config.args.output

    Profiler.start()

    video_path = fname
    
    # initializes cache
    cache = Cache(level=Config.args.cache_level)
    cache_file = None

    #set cache file to save to if specified 
    #otherwise just use cache in memory
    if Config.args.cache_file is not None:
        os.makedirs(Config.args.cache_dir, exist_ok=True)
        cache_file = os.path.join(Config.args.cache_dir, Config.args.cache_file)
    cache.set_save_file(cache_file)

    # load cache from disk if specified
    # mainly used in debugging/developing
    if Config.args.load_cache_file is not None:
        os.path.join(Config.args.cache_dir, Config.args.load_cache_file)
        cache.load(Config.args.load_cache_file)


    # Highlighting the subtitles
    highlighter = ChatGPTHighlighter(video_path,model=Config.args.gpt_highlighting_model, cache=cache, sub_model=Config.args.subtitle_model, num_clips=Config.args.num_clips)
    intervals = highlighter.highlight_intervals()
    cache.save(cache_file)

    # Cropping the video
    cropper = AVASD(video_path, intervals, cache=cache)
    clips = cropper.crop()
    cache.save(cache_file)

    # Adding pizzazz to the subtitles
    creator = VideoProcessor(clips, cache = cache)

    
    if not Config.debug_mode:
        #TODO remove this section entirely
        #needs to be merged into render 
        #also make size an input arg

        #resize the output video
        creator.add_pizzazz(ResizeCreator(new_size=(1080,1920),cache=cache))

    #add Subtitle Writer to pizzazz
    creator.add_pizzazz(SubtitleCreator(cache=cache))

    #render the output clips
    creator.render(output_dir=out_dir)

    Profiler.stop()
    

if __name__ == "__main__":#
    main()
