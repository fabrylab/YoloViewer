import numpy as np
import sys
import configparser
# camera libraries
from pypylon import pylon
from pypylon import genicam
from includes.MemMap import MemMap
import matplotlib.pyplot as plt

# signal handling for grace full shutdown
import signal
# time
import datetime
# include
#from includes.dotdict import dotdict



import os
import psutil


# set the priority for this process
psutil.Process(os.getpid()).nice(psutil.HIGH_PRIORITY_CLASS)

# setup ctrl + c handler
run = True
def signal_handler(sig, frame):
    global run  # we need to have this as global to work
    print("Ctrl+C received")
    print("Shutting down PylonStreamer ...")
    run = False
signal.signal(signal.SIGINT, signal_handler)

#read config
config = configparser.ConfigParser()
config.read("cfg/config.txt")
transpose_image = config["camera"]["transpose_image"] == "True"
flip_x = config["camera"]["flip_x"] == "True"
flip_y = config["camera"]["flip_y"] == "True"

""" PARAMETER """
# select the correct camera mmap cfg here
output_mmap = config["camera"]["output_mmap"]
settings_mmap = config["camera"]["settings_mmap"]

# Setup USB Camera access via Pylon
camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.Open()

# activate chunkmode for frame timestamps, gain and exposure values
camera.ChunkModeActive = True
camera.ChunkSelector = "Timestamp"
camera.ChunkEnable = True
camera.ChunkSelector = "Gain"
camera.ChunkEnable = True
camera.ChunkSelector = "ExposureTime"
camera.ChunkEnable = True

# set camera parameters for Exposure and Gain control
# camera.ExposureAuto = "Continuous"
# TODO we need to expose these values if we want to change them during runtime
camera.AutoExposureTimeLowerLimit = 30.0     # micro seconds
camera.AutoExposureTimeUpperLimit = 1800     # micro seconds
camera.GainAuto = "Continuous"
camera.AutoTargetBrightness = 0.5
camera.AutoGainLowerLimit = 0
camera.AutoGainUpperLimit = 36
camera.AcquisitionFrameRateEnable = True
camera.ExposureTime = 30


# init memmory map output
mmap = MemMap(output_mmap)
smap = MemMap(settings_mmap)
# start continous acquisition, default as Freerun
camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
while not camera.IsGrabbing():
    print('waiting for camera to start')

if (smap.framerate)>0:
    framerate = float(smap.framerate)
    camera.AcquisitionFrameRate = framerate
else:
    framerate = camera.ResultingFrameRate.Value
    smap.framerate = framerate


dropped_counter = 0
index = 0


#? #TODO
#recording_index = 0
#burst_frames = 1

slot = 0
run = True
while camera.IsGrabbing() and run:
    grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

    if grabResult.GrabSucceeded():
        #recording_index += 1
        TimeStampCam = grabResult.GetTimeStamp()
        #print(TimeStampCam)
        image = grabResult.Array

        #if recording_index % int(np.round(camera.ResultingFrameRate.Value / target_framerate)) >= burst_frames:
        #    continue

        index += 1
        slot = (slot + 1) % len(mmap.rbf)

        if transpose_image is True:
            image = image.T
        if flip_y is True:
            image = image[::-1, ::]
        if flip_x is True:
            image = image[:, ::-1]
        mmap.rbf[slot].image[:, :, :] = image[:, :, None]
        mmap.rbf[slot].time_unix = TimeStampCam // 1e9  # floor to remove microseconds
        mmap.rbf[slot].time_us = TimeStampCam // 1e3 % 1e6  # microseconds timestamp
        #mmap.rbf[slot].time_us = TimeStampCam
        mmap.rbf[slot].counter = index

        if index % framerate == 0:
            gain = grabResult.ChunkGain.Value
            smap.gain = gain
            # only set the framerate if it is different
            if float(smap.framerate) != framerate:
                framerate = float(smap.framerate)
                camera.AcquisitionFrameRate = framerate
            print('skipped: ', grabResult.GetNumberOfSkippedImages(), \
                  '\t gain: ', gain, \
                  '\t framerate: ', camera.ResultingFrameRate.Value, \
                  '\t target framerate: ',framerate,smap.framerate ,camera.AcquisitionFrameRate.Value\
                  )
        continue

    else:
        # in case of an error
        print("Err: %d\t - %s" % (grabResult.GetErrorCode(), grabResult.GetErrorDescription()))
        dropped_counter += 1

    grabResult.Release()











