#!/home/paul/Documents/3DMZ/GruttoGras/Software/Main/Jetson/env/bin/python

import serial
from enum import Enum, auto
import serial_asyncio
import asyncio
from typing import Union
import config
import os

DEVICE_FOLDER = "/dev/serial/by-id"

class SerialReader(asyncio.Protocol):
    _newline_callback = None

    def connection_made(self, transport):
        """Store the serial transport and prepare to receive data.
        """
        self.transport = transport
        self.buf = bytes()


    def connection_lost(self):
        print("connection lost")
    
    def data_received(self, data):
        """Store characters until a newline is received.
        """
        self.buf += data
        if b'\r\n' in self.buf:
            lines = self.buf.split(b'\r\n')
            self.buf = lines[-1]  # whatever was left over
            #ignore data while callback is not set
            if self._newline_callback:
                for line in lines[:-1]:
                    try:
                        decoded = line.decode()
                        self._newline_callback(decoded)
                    except:
                        continue

    @property
    def newline_callback(self):
        return self._newline_callback

    @newline_callback.setter
    def newline_callback(self, callback):
        self._newline_callback = callback