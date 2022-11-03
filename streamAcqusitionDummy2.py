import numpy as np
import sys

# camera libraries
# signal handling for grace full shutdown
import signal
# time
import datetime
# include
from includes.MemMap import MemMap
import configparser
import imageio
import time

config = configparser.ConfigParser()
config.read("cfg/config.txt")

# setup ctrl + c handler
def signal_handler(sig, frame):
    global run  # we need to have this as global to work
    print("Ctrl+C received")
    print("Shutting down PylonStreamer ...")
    run = False

signal.signal(signal.SIGINT, signal_handler)

""" PARAMETER """
# select the correct camera mmap cfg here
output_mmap = config["camera"]["output_mmap"]
settings_mmap = config["camera"]["settings_mmap"]

# init memmory map output
mmap = MemMap(output_mmap)
smap = MemMap(settings_mmap)

# start continious acquisition, default as Freerun
timings = []
counter = 0
slot = 0

run = True
index = 0

buffer_size = len(mmap.rbf)

framerate = 50
smap.framerate = framerate

print("Reader")
images = imageio.get_reader(r"2021_08_12_15_21_30.tif")
current_time = time.time()
print(current_time)

while run:

    for image in images:
        framerate = smap.framerate
        print('framerate', framerate)
        print('img')
        start = time.time()

        index += 1
        slot = (slot + 1) % buffer_size

        TimeStampCam = start * 1e9

        mmap.rbf[slot].image[:, :, :] = image[:, :, None, 0]
        mmap.rbf[slot].time_unix = int(start)  # TimeStampCam//1000000000  # floor to remove microseconds
        mmap.rbf[slot].time_us = TimeStampCam // 1000 % 1000000  # microseconds timestamp
        mmap.rbf[slot].counter = index

        timeUsed = time.time() - start
        if 1/framerate - timeUsed > 0:
            time.sleep(1/framerate - timeUsed)

        #current_time += dt
        #if current_time-last_time < 1/framerate:
        #    continue
        #print("wait")
        #while time.time()-last_time < 1/framerate:
        #    time.sleep(0.0001)
        #last_time = current_time
        ##last_time = time.time()
        #TimeStampCam = last_time*1e9
        #print(TimeStampCam, index)


