# Clipy: Shortform Hyper Intelligent Trimming

Clipy is a powerful tool that automatically produces shortform content from long form content and uploads it to your favorite video sharing platform.

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
    * Resolution
    * Shot Cutting Parameters
    * tweak gpt system prompts
- [ ] Create As Module
    * make sure it's usable out of the box
    * find a way to easily distribute model weights

