from collections import namedtuple
import cv2

#container tuple for frames captured from the zed camera
#rgb contains the color image
#df contains the depth image  in float values
#di contains the depth image in uint8 values (should only be used for displaying)
ZedCameraFrame = namedtuple("zed_camera_frame", ["rgb", "df", "di"])

class NullCam(object):
    
    def __init__(self):
        ...

    def get_camera_frames(self) -> ZedCameraFrame:
        photo = cv2.imread("photo.png")
        depth = cv2.imread("depth.png")
        return photo, None, depth