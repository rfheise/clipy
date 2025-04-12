# Clipy: Shortform Hyper Intelligent Trimming
Clipy converts long form content into BRAINROT

# Overview

Clipy takes long form content and produces several short form video clips

## Demo 

Demo Video
[![Watch the Demo Video](https://api.habits.heise.ai/media/other/video2.jpg)](https://www.youtube.com/watch?v=y4C2XMpcZLY)

For More Demos


# TalkNet Active Speaker Detection Demo

[![Watch the Demo Video](https://api.habits.heise.ai/media/other/video1.jpg)](https://www.youtube.com/watch?v=r59jHQHsje8)

## Features
* Automatically highlights the most interesting moments in a video
* Crops the video around the person speaking
* Adds PIZZAZZ to the output video 
    * Subtitles
    * 1080 Rendering
    * More on the way

# Installation 

## Requirements

```
ffmpeg (for rendering the video)
openai api key (content highlighting) ~ uses $0.005/hr of video
requirements in requirements.txt
```
 
## Installation Steps

```
git clone https://github.com/rfheise/clipy.git
cd clipy
pip3 install -r requirements.txt
```

## Usage 

```
python3 -m clipy.main <optional arguments> <input file> <output directory>
```

The input video has to be 25fps constant frame rate and the audio has to be sampled at 16000hz. Making this work with any kind of video file is in the to do list. This could easily be resolved by slapping on a ffmpeg render before clipy is ran but to maintain the original video quality it would take forever to run. You can format your input video using HandBrake.

## Additional Arguments

TODO make it easy to tweak model params with arguments

## Information about running

Cost, plans, etc...

# Acknowledgements  
The TalkNet & S3FD model weights and some preprocessing steps are modifed from this [repository](https://github.com/TaoRuijie/TalkNet-ASD)

# Contact 
For any questions, comments, or suggestions my email is ryan@heise.ai


