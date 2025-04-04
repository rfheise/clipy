import cv2 

def draw_box_on_frame(frame, center, box_size=(100, 100), color=(0, 0, 0), thickness=2):
    """
    Draws a rectangle (box) on the frame with the center at 'center'.
    
    Parameters:
      frame (numpy.ndarray): The input image (frame).
      center (tuple): The (x, y) coordinates of the center of the box.
      box_size (tuple): The (width, height) of the box.
      color (tuple): The BGR color for the box.
      thickness (int): The thickness of the box lines.
    
    Returns:
      numpy.ndarray: The modified frame with the drawn box.
    """
    x, y = center
    width, height = box_size
    # Calculate top-left and bottom-right coordinates from the center point.
    top_left = (int(x - width / 2), int(y - height / 2))
    bottom_right = (int(x + width / 2), int(y + height / 2))
    # Make a copy so the original frame is not modified.
    # frame_with_box = frame.copy()
    frame_with_box = frame
    cv2.rectangle(frame_with_box, top_left, bottom_right, color, thickness)
    return frame_with_box

def write_video(frames, output_path, fps=24):
    """
    Writes a list of frames (numpy arrays) to a video file.
    
    Parameters:
      frames (list): List of frames (numpy arrays).
      output_path (str): Path to the output video file.
      fps (int): Frames per second for the output video.
    """
    # Get dimensions from the first frame.
    height, width = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # You can choose another codec if desired.
    video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    for frame in frames:
        video_writer.write(frame)
    
    video_writer.release()
