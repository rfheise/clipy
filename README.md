# Clipy: Shortform Hyper Intelligent Trimming

Clipy is a powerful tool that automatically produces shortform content from long form content and uploads it to your favorite video sharing platform.

# Outline
I intent to create a modular pipeline that lets me plug and play with various algorithms for the various components. Below I will outline the pipeline and the initial implementation. 

1. Interesting Content Highlighting
    Takes in video and outputs timestamps of interesting moments in the video that would make good clips
    * Moment Detection: Initially implemented as a light weight LSTM

2. Automatic Cropping Around Most Interesting Element 
    Takes in timestamps & video and outputs cropped videos around the most interesting element.
    * Video Highlighting Detector: Initially implemented as TalkNet that identifies the speaker it will yield the cordinates of the detected face
    * Video cropping: crops videos around cordinates probably using opencv or something

3. Pizzazz
    Takes in cropped videos and add subtitles, music, etc...
    * Pizzazz: generic module that takes in cropped video and adds pizzazz 
        * initially just adding subtitles

4. Upload
    Automatically uploads content to video platform if it passes quality check and uploads it to platform. 
    * I intend to automate this part but it will initially be performed manually 

