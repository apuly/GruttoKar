#!/home/paul/Documents/3DMZ/GruttoGras/Software/Main/Jetson/env/bin/python
"""
This module has been set up for the gruttogras project of the 3DMAKERSZONE in Haarlem.

It has the following jobs:
    1. Communicatie with the attached arduino for sensor data
    2. Communicatie with the ZED camera api to get camera images
    3. Syncronise the arduino and zed images
    4. Display all information on screen

The communication with the arduino is asyncronous: we don't know when data is coming in and we don't know when we send data
This issue has been solved by using asyncio. A worker thread constantly checks if new data comes in. When it does, it is automatically passed on.
"""

import asyncio 
from kar import GruttoKar
from zed_camera import ZedCam
from null_camera import NullCam
from webcam_camera import Webcam
from display import GruttoDisplay
import config
import multiprocessing as mp
import argparse
import csv
from gps import GruttoGPS
from datawriter import SensorDataWriter
from datetime import datetime
import os
import cv2

class GruttoGras(object):
    def __init__(self, display, serial, cam, gps):
        self._display = display
        self._serial = serial
        self._cam_class = cam
        self._gps = gps
        
        self._writer: SerialDataWriter = None
        self._gps_coords = (0, 0)
        self._prev_laser_state = None
        self._measure_state: bool = False

        self._camera_frames = None

    #START CODE FOR READING CAMERA
    @staticmethod
    def camera_proces(cam_class, queue: mp.Queue):
        cam = cam_class()
        while True:
            frames = cam.get_camera_frames()
            queue.put(frames)

    def cam_receiver(self, loop, mp_queue: mp.Queue):
        while True:
            frames = mp_queue.get()
            loop.create_task(self.handle_frames(frames))

    async def handle_frames(self, frames):
        self._display.set_frames(frames)
        self._camera_frames = frames

    async def camera_loop(self):
        loop = asyncio.get_event_loop()
        mp_queue = mp.Queue(5)
        loop.run_in_executor(None, self.cam_receiver, loop, mp_queue)
        process = mp.Process(target=self.camera_proces, args=(self._cam_class, mp_queue,))
        process.start()
    #END CODE FOR READING CAMERA

    def on_serial_newline_callback(self, data: str):
        if data.startswith(":"):
            #handle distance measurement
            distance = data[1:]
            lasers = None
        elif data.startswith(">"):
            #handle command response
            print(data)
        else:
            #handle distance and laser state measurement
            split = data.split(" ")
            lasers = split[:config.NUM_LASER_SENSORS]
            distance = split[config.NUM_LASER_SENSORS]

        self._display.measure_distance = distance
        if self._measure_state:
            if lasers is not None:
                self._writer.write_all(float(distance), lasers, self._gps_coords)
            else:
                #if lasers is None, only encoder was received, and thus only encoder can be written 
                self._writer.write_distance(float(distance), self._gps_coords)
            
    def _start_measurement(self):
        self._measure_state = True
        self._display.show_file_saved = False
        now = datetime.now()
        now_s = now.strftime("%Y-%m-%d %H-%M-%S")
        folder_name = f"{config.DATA_DIRECTORY}/{now_s}"
        os.mkdir(folder_name)
        writer = SensorDataWriter(folder_name, "data.csv", config.NUM_LASER_SENSORS)
        self._writer = writer

    def _stop_measurement(self):
        self._measure_state = False
        folder = self._writer.dir.split("/")[-1]
        self._display.file_saved_name = folder
        self._display.show_file_saved = True
        self._writer.close()

    def on_gui_measure_button(self, new_state: bool):
        self._reset_measurement()
        if new_state:
            self._start_measurement()
        else:
            self._stop_measurement()

    def on_gui_reset_button(self):
        self._reset_measurement()

    def _reset_measurement(self):
        self._serial.write('r')
        self._display.measure_distance = 0.0
    
    def gps_line_callback(self, gps):
        if hasattr(gps, "lat") and hasattr(gps, "lon"):
            if gps.lat != "" and gps.lon != "":
                self._display.show_no_gps = False
                self._gps_coords = (gps.lat, gps.lon)
   
    def on_gui_photo_button(self):
        if not self._measure_state:
            return #do nothing if meaure not active

        photo_dir = f"{self._writer.dir}/photos"
        depth_dir = f"{self._writer.dir}/depth"
        depth_img_dir = f"{self._writer.dir}/depth_img"

        dirs = [photo_dir, depth_dir, depth_img_dir]
        for d in dirs:
            if not os.path.isdir(d):
                os.mkdir(d)

        now = datetime.now()
        now_s = now.strftime("%Y-%m-%d %T")
        cv2.imwrite(f"{photo_dir}/{now_s}.png", self._camera_frames[0])
        cv2.imwrite(f"{depth_dir}/{now_s}.png", self._camera_frames[1])
        cv2.imwrite(f"{depth_img_dir}/{now_s}.png", self._camera_frames[2])
    
    async def run(self):
        loop = asyncio.get_event_loop()

        self._display.measure_button_callback = self.on_gui_measure_button
        self._display.reset_button_callback = self.on_gui_reset_button
        self._display.photo_button_callback = self.on_gui_photo_button
        self._gps.gps_line_callback = self.gps_line_callback
        self._serial.newline_callback = self.on_serial_newline_callback

        arduino_task = asyncio.ensure_future(self._serial.async_run(loop))
        gps_task = asyncio.ensure_future(self._gps.async_run(loop))
        await asyncio.gather(self.camera_loop(), gps_task, arduino_task, self._display.run_async())

def build_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--nullcam", action="store_true")
    parser.add_argument("--minimized", "-m", action="store_false")
    return parser.parse_args()

def main():
    mp.set_start_method("spawn")
    args = build_args()

    ser: GruttoKar = GruttoKar.from_dev(config.ARDUINO_DEV_STRING)
    gps: GruttoGPS = GruttoGPS.from_dev(config.GPS_DEV_STRING)
    disp: GruttoDisplay = GruttoDisplay(args.minimized)
    
    if (args.nullcam):
        cam = NullCam
    else:
        cam = ZedCam

    grutto = GruttoGras(disp, ser, cam, gps)
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(grutto.run())

if __name__ == "__main__":
    main()
