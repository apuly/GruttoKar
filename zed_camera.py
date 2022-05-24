from collections import namedtuple
from pyzed import sl
import cv2
import numpy as np
import pickle

#container tuple for frames captured from the zed camera
#rgb contains the color image
#df contains the depth image  in float values
#di contains the depth image in uint8 values (should only be used for displaying)
ZedCameraFrame = namedtuple("zed_camera_frame", ["rgb", "df", "di"])

class ZedCam(object):
    res = sl.Resolution()
    res.width = 1280
    res.height = 720

    #res = sl.RESOLUTION.HD720
    #print(dir(res.value))
    depth_zed = sl.Mat(res.width, res.height, sl.MAT_TYPE.F32_C1, sl.MEM.CPU)
    rgb_image = sl.Mat(res.width, res.height, sl.MAT_TYPE.U8_C3)
    img_cloud = sl.Mat(res.width, res.height, sl.MAT_TYPE.U8_C4)

    def __init__(self):
        init = sl.InitParameters(camera_resolution=sl.RESOLUTION.HD720,
                                    depth_mode=sl.DEPTH_MODE.QUALITY,
                                    coordinate_units=sl.UNIT.METER,
                                    coordinate_system=sl.COORDINATE_SYSTEM.RIGHT_HANDED_Y_UP)
        
        self.zed = sl.Camera()
        status = self.zed.open(init)

        if status != sl.ERROR_CODE.SUCCESS:
            print("Error launching: "+repr(status))
            exit(1)

    def get_camera_frames(self) -> ZedCameraFrame:
        depth_zed = self.depth_zed
        rgb_image = self.rgb_image
        img_cloud = self.img_cloud
       
        if self.zed.grab() == sl.ERROR_CODE.SUCCESS:
            self.zed.retrieve_measure(depth_zed, sl.MEASURE.DEPTH)
            depth_float = depth_zed.get_data()
            
            self.zed.retrieve_image(img_cloud, sl.VIEW.DEPTH)
            depth_img = img_cloud.get_data()
            depth_img_2d = depth_img[:, :, 0]
            depth_color = cv2.applyColorMap(depth_img_2d, cv2.COLORMAP_JET)
            
            self.zed.retrieve_image(img_cloud, sl.VIEW.LEFT)
            img_alpha = img_cloud.get_data()
            img = img_alpha[:, :, :3]

            return (img, depth_float, depth_color)
