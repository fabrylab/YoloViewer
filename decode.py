import configparser
import matplotlib.pyplot as plt
from includes.MemMap import MemMap
import numpy as np
from yolo.model import build_net,predict

import signal

# setup ctrl + c handler
run = True
def signal_handler(sig, frame):
    global run  # we need to have this as global to work
    print("Ctrl+C received")
    print("Shutting down Decoder ...")
    run = False
signal.signal(signal.SIGINT, signal_handler)

#read config
config = configparser.ConfigParser()
config.read("cfg/config.txt")
output_mmap = config["camera"]["output_mmap"]
settings_mmap = config["camera"]["settings_mmap"]
smap = MemMap(settings_mmap)
#mmap = MemMap(output_mmap)


#first_ts_s = mmap.rbf[0].time_unix
#first_ts_us = mmap.rbf[0].time_us
#print(first_ts_s,first_ts_us)
import tensorflow as tf


framerate = smap.framerate
sleeptime = 1/framerate




def decodeNP(preds):
    anchorLevelIds = np.concatenate(
        [np.ones((p[..., 0] > thresholdOpt).sum(), dtype=int) * i for i, p in enumerate(preds)])
    imageId, yId, xId = np.concatenate([np.array(np.where(p[..., 0] > thresholdOpt)) for p in preds], axis=1)
    c, x, y, w, h, p = np.concatenate([p[p[..., 0] > thresholdOpt] for p in preds], axis=0).T
    anchorSizes = downsamples[anchorLevelIds]
    X = (xId + x) * anchorSizes
    Y = (yId + y) * anchorSizes
    W = w * anchorSizes / anchorOverlap
    H = h * W
    angle = p * 180
    # with timer("NMS"):
    NMSthreshold = 1
    distN = ((X[:, None] - X[None, :]) ** 2 + (Y[:, None] - Y[None, :]) ** 2) / (W[:, None] * W[None, :])
    NM = ((NMSthreshold * np.eye(len(X)) + distN) < NMSthreshold) & (c[:, None] < c[None, :]) & (
            imageId[:, None] == imageId[None, :])
    # with timer("export to numpy"):
    #all_data.extend(np.stack([X, Y, W, H, angle, imageId]).T[~np.any(NM, axis=1)])
    return np.stack([X, Y, W, H, angle, imageId]).T[~np.any(NM, axis=1)]


#mmap = MemMap("./cfg/prediction.xml")
while run:
    img = None
    meta_data = {}
    #tstart = datetime.datetime.now()
    #imList, metaList = image_buffer.getNOldestImags(N=64)

    #while img is None:
        #img, meta_data = image_buffer.getNewestImage()
    #else:
        #ts = meta_data.pop("timestamp_us")

    from time import  time
    start0 = time()
    images, meta_data = image_buffer.getNOldestImags(N=32)
    print("load",time()-start0)
    #pred = model.predict(images)
    start1 = time()
    pred = model(images)
    print("pred",time()-start1)
    print("images per second:",len(images)/(time()-start0))
    #start = time()
    #dec = decodeNP(pred)
    #print(time()-start)
    #pred = model(images)
    #all_data = predict(model,images,th=thresholdOpt,downsamples=downsamples,anchorOverlap=anchorOverlap)

#    if len(images) < batch_size:
#        images.append(img)
#    else:
#        images = np.array(images)
#        images = np.repeat(images[..., None], 3, axis=-1)
#        images = []
#        all_data = predict(model,images,th=thresholdOpt,downsamples=downsamples,anchorOverlap=anchorOverlap)
#        print(all_data)
#        #yolo (images)

