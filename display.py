#!/usr/bin/python3

import sys
import cv2
import numpy as np
from datetime import datetime
from enum import Enum
import asyncio

class View(Enum):
    color = 0
    depth = 1

BTN_CAPTURE = 'b'
BTN_QUIT = 'q'
BTN_SWITCH_VIEW = 'v'

PHOTO_FOLDER = "captures"

class GruttoDisplay(object):
    _color = None
    _depth = None
    _display_mode = View.color
    WINDOW_NAME = "GrasMeter"

    CAM_AREA = ((186, 14), (1011, 414))    


    def __init__(self, fullscreen=True):
        cv2.namedWindow(self.WINDOW_NAME, cv2.WINDOW_NORMAL)
        if fullscreen:
            cv2.setWindowProperty(self.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.setMouseCallback(self.WINDOW_NAME, self.mouse_callback)
        self.background = cv2.imread('ui.png')
        self.view_mode: View = View.color
        self.measure_active: bool = False
        self.measure_distance: float = 0.0

        self.file_saved_name: str = ""
        self.show_file_saved: bool = False
        self.show_no_gps: bool = True

        self.BTNS = (
            ((14, 15), (174, 297), self.switch_view),
            ((14, 309), (174, 590), self.btn_measure),
            ((833, 433), (1011, 590), self.btn_reset),
            self.CAM_AREA+(self.btn_photo,)
        )

        self._measure_button_callback = None
        self._reset_button_callback = None
        self._photo_button_callback = None

    @property
    def photo_button_callback(self):
        return self._photo_button_callback

    @photo_button_callback.setter
    def photo_button_callback(self, callback):
        self._photo_button_callback = callback

    @property
    def reset_button_callback(self):
        return self._reset_button_callback

    @reset_button_callback.setter
    def reset_button_callback(self, callback):
        self._reset_button_callback = callback

    @property
    def measure_button_callback(self):
        return self._measure_button_callback

    @measure_button_callback.setter
    def measure_button_callback(self, callback):
        self._measure_button_callback = callback

    def set_frames(self, frames):
        self._color, _, self._depth = frames

    def load_cam_frame(self):
        size_x = self.CAM_AREA[1][0] - self.CAM_AREA[0][0]
        size_y = self.CAM_AREA[1][1] - self.CAM_AREA[0][1]
        
        image = self._color if self.view_mode == View.color else self._depth
        resized = cv2.resize(image, (size_x, size_y), interpolation=cv2.INTER_LINEAR)
        return resized

    def build_ui(self):
        #LOAD BASE FRAME
        base = cv2.imread("ui.png")

        #ADD CAMERA FRAME
        frame = self.load_cam_frame()
        base[
            self.CAM_AREA[0][1]:self.CAM_AREA[1][1],
            self.CAM_AREA[0][0]:self.CAM_AREA[1][0],
            :
        ] = frame
        #END ADDING CAMERA FRAME

        #ADD MEASUREMENT TEXT
        if not self.measure_active:
            measure_text = "INACTIVE"
            base = cv2.putText(base, measure_text, (846, 510), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0,0,0,), thickness=2)
        else:
            base = cv2.putText(base, "MEASURED", (846, 510), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0,0,0,), thickness=2)
            base = cv2.putText(base, f"{self.measure_distance}m", (846, 538), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0,0,0,), thickness=2)
        #END ADD MEASUREMENT TEXT

        #ADD DATA SAVED TEXT
        if not self.measure_active and self.show_file_saved:
            base = cv2.putText(base, f"Saved to \"{self.file_saved_name}\"", (220, 510), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0,0,0,), thickness=2)
        #END DATA SAVED TEXT

        #ADD NO SATALITE TEXT
        if self.show_no_gps:
            base = cv2.putText(base, "No GPS Connection", (220, 480), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.9, (0,0,0,), thickness=2)

        return base

    def build_waitscreen(self):
        base = cv2.imread("3dmzlogo.png")
        base = cv2.resize(base, (1024, 600))
        return base
    
    def tick(self):
        if not(self._color is None or self._depth is None):
            cv2.imshow(self.WINDOW_NAME, self.build_ui())
        else:
            cv2.imshow(self.WINDOW_NAME, self.build_waitscreen())

    def switch_view(self, *args):
        if self.view_mode == View.depth:
            self.view_mode = View.color
        else:
            self.view_mode = View.depth
    
    def btn_measure(self):
        self.measure_active = not self.measure_active
        if self._measure_button_callback:
            self._measure_button_callback(self.measure_active)

    def btn_photo(self):
        print("photo")
        if self._photo_button_callback:
            print("callback")
            self._photo_button_callback()

    def btn_reset(self):
        if self._reset_button_callback:
            self._reset_button_callback()

    def mouse_callback(self, action, x, y, btn, *args):
        if action == 1: #if mouse is pressed
            for btn in self.BTNS:
                within_x = btn[0][0] < x < btn[1][0]
                within_y = btn[0][1] < y < btn[1][1]
                if within_x and within_y:
                    btn[2]()

    async def run_async(self):
        while True:
            self.tick()
            key = cv2.waitKey(1)
            if key == ord('q'):
                import os
                os.popen("pkill python")
            await asyncio.sleep(0.033)

if __name__ == "__main__":
    import asyncio
    #from webcam_camera import Webcam
    from null_camera import NullCam
    from zed_camera import ZedCam
    from concurrent.futures import ProcessPoolExecutor
    import multiprocessing as mp
    
    def camera_proces(queue):
        cam = ZedCam()
        while True:
            frames = cam.get_camera_frames()
            queue.put(frames)

    def cam_receiver(loop, async_queue, mp_queue):
        while True:
            frames = mp_queue.get()
            loop.create_task(async_queue.put(frames))


    async def main():
        disp = GruttoDisplay()
        await asyncio.gather(capture_loop(disp), disp.async_run())

    def cam_thread(loop, queue):
        cam = ZedCam()
        while True:
            frames = cam.get_camera_frames()
            loop.create_task(queue.put(frames))
   
    async def capture_loop(disp: GruttoDisplay):
        loop = asyncio.get_event_loop()
        #cam = ZedCam()
        mp_queue = mp.Queue(1)
        async_queue = asyncio.Queue(1)
        loop.run_in_executor(None, cam_receiver, loop, async_queue, mp_queue)
        process = mp.Process(target=camera_proces, args=(mp_queue,))
        process.start()

        while loop.is_running():
            frames = await async_queue.get()
            disp.set_frame(frames)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

