# Overview

Developer information for clipy

**ALL EDITS MUST** maintain the modularity functionality of the pipeline

Being able to modify a section of the pipeline is as simple as inheriting the core class for that section of the pipeline and overloading the primary functions. 

I want to get to a point where each section of the pipeline has several different implementations and the end user can determine what backend they want to use for each component.

# TODOS

## Minor Edits/Tweaks

- [X] Finish Prototype implementation
- [ ] Optimize Code
    - [ ] Use torch data loaders for batched inference - S3FD and Talknet
        - [X] S3FD
        - [ ] TalkNet
    - [ ] Tweak Settings For Optimal Performance
        - [ ] TalkNet
        - [ ] S3FD
        - [X] ffmpeg renders
        - [ ] scene detection
        - [X] ChatGPT system prompt
        - [ ] subtitle generation
    - [ ] Try different subtitle presets for optimal performance
    - [ ] Try different parameters for scene-detection library
- [X] Clean/Comment Code
- [ ] Clean/Comment Frame Buffer Code
- [X] Remove Cosmetic Inefficiencies In Code 
    - [X] Make data flow top -> down rather than all over the place
    - [ ] Review the code to make sure everything makes sense
- [ ] Make sure it's usable out of the box
    - [ ] Create as a python module
    - [X] find a way to easily distribute model weights
    - [X] Replace lame with ffmpeg call
    - [ ] Docker Container?

## Bug Fixes

### Major
    None

### Moderate

- [ ] Fix subtitle alignment using something like aeneas
    * Consider breaking up large subtitle blocks during render
- [ ] Make it so scene has several centers depending on main track in focus
    * this will make the cropping look a lot more natural

### Minor
- [ ] Add margin to facial cropping
    * currently it will zoom in on a speakers face if they take up a majority of the frame
- [ ] Fix jitteriness with static speaker
    * caused by cropping on scenes from scene detector
    * fix by merging centers across scenes if they are within some distance threshold of each other


### Recently Completed

- [X] Fix debug mode bug that causes bboxes to be in BGR instead of RGB
- [X] Add resizing to rendering process this will get rid of pixelated output
    * right now it is cropping then resizing but these results in unnecessary quality loss
    * should resize and then crop instead of crop and then resize
- [X] Fix issue with 1080P video eating up all the ram
    * Create a raw frames object to manage raw frames
    * Have it abstract all the io
    * create a buffer with max buffer size under the hood to manage reading/writing frames to disk

## Features

These features are sorted by the value they provide to the project i.e. the ones that will yield the highest improvements per estimated time they will take to implement

### Major

- [ ] ✨Professionalism✨
    - [ ] Unit Tests
        - [ ] Global
        - [ ] Content Highlighting
        - [ ] AutoCropper
        - [ ] Rendering/Pizzazz
    - [ ] Github Stuff
        - [ ] Make first beta release
        - [ ] Implement github actions that run unit tests when a commit is pushed to main

- [ ] Make AutoCropping better
    * improve cropping for stream clips
        * layer the streamer/content in crop window
    * each scene will have a list of lists of centers 
        * each center will correspond with a speaker
        * if several speakers talk at the time considering layering them

- [ ] Add a content highlighter that runs locally 
    * GPT query feels like a grift 
    * current gpt performance if mediocre


### Moderate

- [ ] Background Music Based Upon Mood
- [ ] Speaker Diarization For Subtitles
        - [ ] Use cached output from talknet with a siamese network?
- [ ] Auto Uploading
    * Automatically uploads a platform to a platform of your choosing
    * Should be the final step in the pipeline
    * Will implement after I'm confident in the output video quality
- [ ] Quality Control
    * Implement some form of quality control into the pipeline 
    * Reject any videos that fall below quality threshold


### Minor
- [ ] Caching
    * Make a professional cache that saves/loads faster
    * Currently just pickles everything and makes the cache file HUGE
    * Add a save/load func to each core section of the pipeline
- [ ] Implement Professional Logger
- [ ] Implement Professional Config

### Recently Added
- [X] tweak model inputs to work with variable framerate & audio sampling without re-rendering or re-render only needed clips
        - [X] As a band-aid solution re-render facial tracks to appropriate frame rate & audio sampling rate rather than the whole video
- [X] Add custom arguments to main


# The Pipeline

# Content Highlighting

This is the first step in the pipeline. Essentially all it does is take in the input video and identifies the most interesting timestamps in the video that should be turned into clips. 

### Current Implementations  

### ChatGPT Highlighter

* Generates the video subtitles using openai-whisper locally on the device
* sends processed subtitles to chatgpt to determine the most interesting moments 
* makes sure subtitles line up with video cuts
# AutoCropping

This is the second step in the pipeline. It takes in the input video & timestamps of the moments from the video that should be converted into clips. Each output clip returns the rendering information on how to crop the video when it is time to render. 

### Current Implementations

### AVASD (Audio Visual Active Speaker Detection)

### TalkNet Active Speaker Detection Demo

[![Watch the Demo Video](https://api.habits.heise.ai/media/other/video1.jpg)](https://www.youtube.com/watch?v=r59jHQHsje8)


The input video has to be 25fps constant frame rate and the audio has to be sampled at 16000hz to work with TalkNet. Making this work with any kind of video file is in the to do list. I want to try to get TalkNet to work with any kind of input video using padding but that would require re-training talknet. This step could also be removed by only re-rendering the input for TalkNet but that seems like a grift and would take work.

*re-renders input video to be 25fps & 16KHZ
* For each clip it use a pre-trained S3FD model to determine all the facial tracks in the each video cut in the input clip
* Uses TalkNet model to identify the active speakers
    * Takes in the facial tracks and clip audio
    * For each facial track it uses the corresponding audio to determine if that facial track is speaking 
    * I use the TalkNet author's model code to load the pre-trained model and process the inputs 
        * TalkNet generates audio embeddings and facial embeddings across the track and uses cross attention between the video/audio to determine if the person in the track is speaking 
    * [TalkNet Paper](https://arxiv.org/pdf/2107.06592)

# Pizzazz/Rendering

Adds additional content to each generated clip. Uses the custom Video Processor module to render the final output video. 

Each pizzazz takes as input the rendered video frames and audio and outputs it's processed frames and audio. 

### Current Implementations

### Subtitle Creator

Adds subtitles in various colors to the output video. Currently, uses cached subtitles from the initial highlighting step. A more optimized version would generate it's own subtitles using the subtitle utility if the subtitles in the cache are empty.

# Quality Control
This is the fourth step in the pipeline. It takes as input the rendered videos and determines whether or not they meet some kind of quality threshold. 

### Current Implementations

TODO

# Auto Uploading 
This is the final step in the pipeline. It takes as input all of the clips that passed quality control and automatically uploads them to platforms of the users choice.

### Current Implementations 

TODO

# Debug Mode 
This mode is useful for development!

What does debug mode do?

* Caches & Loads Everything 
    * Ensures you don't have to re-execute the entire pipeline to test your feature

* Useful logs
    * Prints useful logging messages
    * Saves facial tracks for S3FD
    * Saves Bounding Boxes for AVASD