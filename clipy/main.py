from .ContentHighlighting import ChatGPTHighlighter
from .AutoCropping import AVASD
from .Pizzazz import VideoProcessor, SubtitleCreator
from .Utilities import Logger, Cache, Timestamp, Profiler
import sys
def main():

    if len(sys.argv) != 4 and not Logger.debug:
        Logger.log_error("Usage: python main.py <video_path> <output_dir> <platform>")
        sys.exit(1)
    
    #TODO use these args instead of hard coded values
    # fname = sys.argv[1]
    # out_dir = sys.argv[2]
    # platform = sys.argv[3]
    Profiler.init()
    Profiler.start()

    video_path = "./videos/other/walk_the_line_25_16.mp4"
    cache = Cache(dev=True)
    cache_file = "./.cache/fd_test.sav"
    cache.set_save_file(cache_file)
    cache.load(cache_file)


    # Highlighting the subtitles
    highlighter = ChatGPTHighlighter(video_path,model="gpt-4o", cache=cache, sub_model="turbo")
    intervals = highlighter.highlight_intervals()
    # intervals.insert(0,Timestamp(1498,1546))
    cache.save(cache_file)

    # Cropping the video
    cropper = AVASD(video_path, intervals, cache=cache)
    clips = cropper.crop()
    cache.save(cache_file)

    # # Adding pizzazz to the subtitles
    creator = VideoProcessor(clips, cache = cache)
    creator.add_pizzazz(SubtitleCreator(cache=cache))
    creator.render(output_dir="clips")
    cache.save(cache_file)

    Profiler.stop()
    

if __name__ == "__main__":
    main()