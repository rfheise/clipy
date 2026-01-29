# Clipy: Shortform Hyper Intelligent Trimming
Clipy converts long form content into BRAINROT

# Overview

Clipy takes long form content and produces several short form video clips

## Demo 

[![Watch the Demo Video](https://api.habits.heise.ai/media/other/video3.jpg)](https://youtube.com/shorts/yBgwHEgNGmw?si=dMmKJubEb-pRLaSR)

[More Demos](https://www.youtube.com/channel/UCX7QM2FDjp6vTTGdy27wv4Q)

### TalkNet - Audio Visual Active Speaker Detection Demo

[![Watch the Demo Video](https://api.habits.heise.ai/media/other/video1.jpg)](https://www.youtube.com/watch?v=r59jHQHsje8)


# Installation 

## Requirements

```
ffmpeg (for rendering the video)
openai api key (content highlighting) ~ uses $0.035/hr of video with o3-mini
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
| --gpt-highlighting-model <model>      | gpt model to use for content highlighting         | o3-mini        |
| --subtitle-model <model>     | subtitle model for generating subtitles (see [openai whisper](https://github.com/openai/whisper) for more info)       | turbo        |
| --num-clips <number> | number of clips to output | ceiling(runtime/5) |
| --debug-mode | runs in debug mode (debug mode runs significantly faster and caches everything but produces very poor quality output) | N/A |
| -h | shows additional configuration options | N/A |

See [Config.py](clipy/Utilities/Config/Config.py) for more details

## Information about running

You need a gpu to run this software efficiently. Right now it takes ~10 minutes to process an hour of content using my 4090 with the turbo subtitle model. It takes ~1.5hrs to process an hour of content on my macbook using the cpu with tiny.en subtitle model. 

You can also try to use gpt-o4-mini (used in debug mode) instead of o3-mini since it's a fraction of the cost. However, I've found that the results are significantly worse. You can also try any other model that you desire but I've found the best performance/cost model to be o3-mini.

# Features
* Automatically highlights the most interesting moments in a video
    * Currently uses chatgpt to highlight the most interesting moments
    * This feels like a grift and I plan on developing/finding a model that can run locally
* Crops the video around the person speaking
* Adds PIZZAZZ to the output video 
    * Subtitles
    * More on the way

# How Does It Work/Developer Information
See [Dev-info.md](Dev-info.md) for more details

# Acknowledgements  
The TalkNet & S3FD model weights and preprocessing steps are modified from this [repository](https://github.com/TaoRuijie/TalkNet-ASD)


