# Clipy: Shortform Hyper Intelligent Trimming

# Requirements 
```
ffmpeg 
lame
requirements in requirements.txt
```
# Running The Editor
```
cd <clipy directory>
pip install -r requirements.txt
python -m clipy.main <in file> <output directory>
```
Currently the input video needs to be 25fps with a 16000hz audio sample rate. Making this run with various input video types is in the todo list. 

The editor will download the model weights while it is running. The weights are hosted on cloudflare and are around 100MB.

Ideally you have a decent gpu to run the editor. With my 4090 it currently takes ~15 minutes to generate 10 clips from a 2 hour video. When I tested it using my m4 mac mini it took ~2 hours to similar results. I'm working on optimizing the gpu speeds but I honestly don't think cpu rendering speeds will improve much. 

# Outline
I intent to create a modular pipeline that lets me plug and play with various algorithms for the various components. Below I will outline the pipeline and the initial implementation. 

1. Interesting Content Highlighting ✅
    Takes in video and outputs timestamps of interesting moments in the video that would make good clips
    * Moment Detection: Initially Implemented As ChatGPT subtitle query

2. Automatic Cropping Around Most Interesting Element ✅
    Takes in timestamps & video and outputs cropped videos around the most interesting element.
    * Video Highlighting Detector: Initially implemented as TalkNet that identifies the speaker it will yield the cordinates of the detected face
    * Video cropping: crops videos around cordinates probably using opencv or something
## TalkNet - Audio Visual Active Speaker Detection
[![Watch the Demo Video](https://api.habits.heise.ai/media/other/video1.jpg)](https://www.youtube.com/watch?v=r59jHQHsje8)


3. Pizzazz ✅
    Takes in cropped videos and add subtitles, music, etc...
    * Pizzazz: generic module that takes in cropped video and adds pizzazz 
        * initially just adding subtitles
## Demo Output

[![Watch the Demo Video](https://api.habits.heise.ai/media/other/video2.jpg)](https://www.youtube.com/watch?v=y4C2XMpcZLY)

4. Upload ✅
    Automatically uploads content to video platform if it passes quality check and uploads it to platform. 
    * I intend to automate this part but it will initially be performed manually 

# TODO

- [ ] Finish Prototype implementation
- [ ] Optimize Code
    * Use torch data loaders for batched inference - S3FD and Talknet
    * see if I can tweak model to work with variable framerate & audio sampling without re-rendering
    * Try different subtitle presets for optimal performance
    * try different parameters for scene-detection library
- [ ] Clean/Comment Code
- [ ] Remove Cosmetic Inefficiencies In Code 
    * Make data flow top -> down rather than all over the place
    * Review the code to make sure everything makes sense
- [ ] Bug Fixes
    * Weird Splits in outputs
        * Should be an easy fix with a min scene duration
        * Merge scenes until they hit min duration
    * Weird Subtitle Outputs
        * strange outputs from openai whisper 
        * not sure how to fix but could slap some band-aids on it and pray they fix it
- [ ] Tweak Video Outputs
    * Custom Fonts
    * Font Size
    * Text Position
    * Resolution
    * Shot Cutting Parameters
    * tweak gpt system prompts
- [ ] Create As Module
    * make sure it's usable out of the box
    * find a way to easily distribute model weights
    * Replace lame with ffmpeg call
    * Docker Container?

