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
[![Watch the Demo Video](https://img.youtube.com/vi/jkNTngzHOxM/0.jpg)](https://www.youtube.com/watch?v=jkNTngzHOxM)


3. Pizzazz ✅
    Takes in cropped videos and add subtitles, music, etc...
    * Pizzazz: generic module that takes in cropped video and adds pizzazz 
        * initially just adding subtitles
## Demo Output

[![Watch the Demo Video](https://img.youtube.com/vi/y4C2XMpcZLY/0.jpg)](https://www.youtube.com/watch?v=y4C2XMpcZLY)

4. Upload ✅
    Automatically uploads content to video platform if it passes quality check and uploads it to platform. 
    * I intend to automate this part but it will initially be performed manually 

# TODO

- [ ] Finish Prototype implementation
- [ ] Optimize Code
- [ ] Clean/Comment Code
- [ ] Remove Cosmetic Inefficiencies In Code 
- [ ] Tweak Video Outputs
    * Custom Fonts
    * Font Size
    * Resolution
    * Shot Cutting Parameters
- [ ] Create As Module
