import cv2
from collections import namedtuple

ZedCameraFrame = namedtuple("zed_camera_frame", ["rgb", "df", "di"])


class Webcam(object):    
    def __init__(self):
        self.cam = cv2.VideoCapture(0)

    def get_camera_frames(self) -> ZedCameraFrame:
        ret, frame = self.cam.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_three = cv2.merge([gray,gray,gray])
        return ZedCameraFrame(frame, None, gray_three)