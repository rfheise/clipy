from ContentHighlighting import SubtitleHighlighter
from AutoCropping import TalkNetCropper 
from Pizzazz import Pizzazz, SubtitleCreator 
from AutoUpload import QualityCheck, AutoUploader
from Utilities import Logger, Cache
import sys

def main():

    if len(sys.argv) != 4:
        Logger.log_error("Usage: python main.py <video_path> <output_dir> <platform>")
        sys.exit(1)
    
    fname = sys.argv[1]
    out_dir = sys.argv[2]
    platform = sys.argv[3]

    # Highlighting the subtitles
    cache = Cache(level = "basic")
    highlighter = SubtitleHighlighter(video_path=fname, subtitle_interval=20, cache = cache)
    intervals = highlighter.highlight_intervals()

    # Cropping the video
    cropper = TalkNetCropper(intervals, video_path=fname, cache = cache)
    videos = cropper.crop()

    # Adding pizzazz to the subtitles
    creator = Pizzazz(videos, cache = cache)
    creator.add_pizzazz(SubtitleCreator(cache = cache))
    creator.process_videos(output_directory=out_dir)

    # Automatically upload to video platform 
    quality_check = QualityCheck(input_dir=out_dir)
    passed_videos = quality_check.check_quality()
    uploader = AutoUploader(passed_videos, platform=platform)
    uploader.upload()

    

if __name__ == "__main__":
    main()