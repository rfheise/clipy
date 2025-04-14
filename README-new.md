# Clipy: Shortform Hyper Intelligent Trimming
Clipy converts long form content into BRAINROT

# Overview

Clipy takes long form content and produces several short form video clips

## Demo 

[![Watch the Demo Video](https://api.habits.heise.ai/media/other/video3.jpg)](https://www.youtube.com/watch?v=nlpSfOkrqXM)

[More Demos](https://www.youtube.com/channel/UCX7QM2FDjp6vTTGdy27wv4Q)


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
pip install -r requirements.txt
```

## Usage 


```
export OPENAI_API_KEY=<insert api key>
python -m clipy.main <optional arguments> -i <input file> -o <output directory>
```



## Additional Arguments


| Flag | Description | Default Value |
| :----------- | :------------: | ------------: |
| --device <device>     | Torch Device For Running Models        | cuda if cuda is detected else cpu      |
| --gpt-highlighting-model <model>      | gpt model to use for content highlighting         | gpt-4o        |
| --subtitle-model <model>     | subtitle model for generating subtitles (using tiny.en significantly reduces the runtime on cpu but diminishes the quality)       | turbo        |
| --num-clips <number> | number of clips to output | ceiling(runtime/5) |
| --debug-mode | runs in debug mode (debug mode runs significantly faster and caches everything but produces very poor quality output) | N/A |
| -h | shows additional configuration options | N/A |

## Information about running

You need a gpu to run this software efficiently. Right now it takes ~10 minutes to process an hour of content using my 4090 with the turbo subtitle model. It takes ~1.5hrs to process an hour of content on my mac mini using the cpu with tiny.en subtitle model. 

You can also try to use gpt-o4-mini instead of gpt-4o since it is 1/10th of the cost. However, I've found that the results are significantly worse. 

# Acknowledgements  
The TalkNet & S3FD model weights and preprocessing steps are modifed from this [repository](https://github.com/TaoRuijie/TalkNet-ASD)

# Contact 
For any questions, comments, or suggestions my email is ryan@heise.ai


