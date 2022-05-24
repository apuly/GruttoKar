import pynmea2
import os
from serialhandler import SerialReader
import asyncio
import config
import serial_asyncio
import serial

class GruttoGPS():
    def __init__(self, serial: str):
        self._reader = SerialReader()
        self._port = serial
        self._gps_line_callback = None

    @property
    def gps_line_callback(self):
        return self._gps_line_callback

    @gps_line_callback.setter
    def gps_line_callback(self, callback):
        self._gps_line_callback = callback

    def on_newline(self, line):
        if self._gps_line_callback:
            gps = pynmea2.parse(line)
            self._gps_line_callback(gps)

    @classmethod
    def from_dev(cls, s):
        DIR = "/dev/serial/by-id"
        for dev in os.listdir(DIR):
            if s in dev:
                dev_path = f"{DIR}/{dev}"
                return cls(dev_path)
                

    def async_run(self, loop):
        self._reader.newline_callback = self.on_newline
        return serial_asyncio.create_serial_connection(loop, lambda: self._reader, self._port, baudrate=9600)
      

if __name__ == "__main__":
    def gps_callback(gps):
        print(gps)

    async def other_loop():
        while True:
            asyncio.sleep(1)

    async def main(loop):
        ser = GruttoGPS.from_dev(config.GPS_DEV_STRING)
        ser.gps_line_callback = gps_callback
    
        task = asyncio.ensure_future(ser.async_run(loop))
        await asyncio.gather(task)
        # while True:
        #     await asyncio.sleep(0.1)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.run_forever()
    # def from_dev(s):
    #     DIR = "/dev/serial/by-id"
    #     for dev in os.listdir(DIR):
    #         if s in dev:
    #             return f"{DIR}/{dev}"
    # dev = from_dev(config.GPS_DEV_STRING)
    # ser = serial.Serial(dev, baudrate=9600)
    # while True:
    #     print(ser.readline())
