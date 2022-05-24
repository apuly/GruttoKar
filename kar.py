import serial_asyncio
import asyncio
import os
from serialhandler import SerialReader

class GruttoKar():
    def __init__(self, serial: str):
        self._reader = SerialReader()
        self._port = serial

    def write(self, c):
        self._reader.transport.write(c.encode("utf-8"))

    @classmethod
    def from_dev(cls, s):
        DIR = "/dev/serial/by-id"
        for dev in os.listdir(DIR):
            if s in dev:
                return cls(f"{DIR}/{dev}")
    
    @property
    def newline_callback(self):
        return self._reader.newline_callback

    @newline_callback.setter
    def newline_callback(self, callback):
        self._reader.newline_callback = callback

    def async_run(self, loop):
        return serial_asyncio.create_serial_connection(loop, lambda: self._reader, self._port, baudrate=115200)
        
class NoDeviceFoundError(Exception):
    pass
