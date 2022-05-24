import config
import csv
import time
from typing import List, Tuple

class SensorDataWriter(object):
    def __init__(self, filename, num_sensor):
        header = ["distance"]
        header += [f"laser{i}" for i in range(num_sensor)]
        header += ["time", "latitude", "longitude"]

        self._num_sensor = num_sensor
        self._file = open(filename, 'w')
        self._filename = filename
        self._writer = csv.writer(self._file)

        self._writer.writerow(header)

        self._prev_laser = [0]*num_sensor
        self._prev_distance = 0

    @property
    def filename(self):
        return self._filename

    def build_data(self, encoder: float, lasers: List[int], gps: Tuple[float, float]):
        print(encoder, lasers, gps)
        now = round(time.time(), 3) #time in milliseconds
        arr =  [encoder]+lasers+[now]+list(gps)
        print(arr)
        return arr

    def write_all(self, encoder: float, lasers: List[int], gps: Tuple[float, float]):
        line = self.build_data(encoder, lasers, gps)
        self._writer.writerow(line)
        self._prev_laser = lasers
        
    def write_distance(self, encoder: float, gps: Tuple[float, float]):
        condition1 = config.REDUNDANT_WRITE_METER == 0
        condition2 = (self._prev_distance+config.REDUNDANT_WRITE_METER) <= encoder
        if condition1 or condition2:
            line = self.build_data(encoder, self._prev_laser, gps)
            self._writer.writerow(line)
            self._prev_distance = encoder
        
    def close(self):
        self._file.close()
