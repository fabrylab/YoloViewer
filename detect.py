import configparser
import matplotlib.pyplot as plt
from includes.MemMap import MemMap
import numpy as np
from yolo.model import build_net,predict
from helper_functions import ImageBuffer
import signal
from time import time
import sqlite3
import tensorflow as tf
from sql_helper import *
import os


os.environ["CUDA_VISIBLE_DEVICES"]="0"

gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        # Currently, memory growth needs to be the same across GPUs
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        logical_gpus = tf.config.experimental.list_logical_devices('GPU')
        print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
    except RuntimeError as e:
        # Memory growth must be set before GPUs have been initialized
        print(e)


# setup ctrl + c handler
run = True
def signal_handler(sig, frame):
    global run  # we need to have this as global to work
    print("Ctrl+C received")
    print("Shutting down Detector ...")
    run = False
signal.signal(signal.SIGINT, signal_handler)

#read config
config = configparser.ConfigParser()
config.read("cfg/config.txt")
output_mmap = config["camera"]["output_mmap"]
settings_mmap = config["camera"]["settings_mmap"]

smap = MemMap(settings_mmap)


#first_ts_s = mmap.rbf[0].time_unix
#first_ts_us = mmap.rbf[0].time_us
#print(first_ts_s,first_ts_us)

#crate database
#create connection to db
db_file = r'C:\Software\YoloViewer\database\detections.db'
clear_db(db_file)
create_table(db_file)

#fetch_all(db_file)
image_buffer = ImageBuffer(output_mmap)

images = []
#initialize yolo
downsamples = np.array([64,])
anchorOverlap = 0.5
H,W,C = 540, 720, 3
batch_size = 16
thresholdOpt = 0.39
baseNetwork = 'efficientnetb0'

model_path = r'yolo/kld.h5'
model = build_net(model_path,H=H,W=W,downsamples=downsamples)

def decode(preds):
    anchorLevelIds = np.concatenate(
        [np.ones((p[..., 0] > thresholdOpt).numpy().sum(), dtype=int) * i for i, p in enumerate(preds)])
    imageId, yId, xId = np.concatenate([tf.where(p[..., 0] > thresholdOpt).numpy() for p in preds], axis=0).T
    c, x, y, w, h, p = np.concatenate([p[p[..., 0] > thresholdOpt].numpy() for p in preds], axis=0).T
    anchorSizes = downsamples[anchorLevelIds]
    X = (xId + x) * anchorSizes
    Y = (yId + y) * anchorSizes
    W = w * anchorSizes / anchorOverlap
    H = h * W
    angle = p * 180
    # with timer("NMS"):
    NMSthreshold = 1
    distN = ((X[:, None] - X[None, :]) ** 2 + (Y[:, None] - Y[None, :]) ** 2) / (W[:, None] * W[None, :])
    NM = ((NMSthreshold * tf.eye(len(X)) + distN) < NMSthreshold) & (c[:, None] < c[None, :]) & (
            imageId[:, None] == imageId[None, :])
    # with timer("export to numpy"):
    all_data.extend(np.stack([X, Y, W, H, angle, imageId]).T[~np.any(NM, axis=1)])

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


slots = np.array([0])

while run:
    img = None
    meta_data = {}
    #tstart = datetime.datetime.now()
    #imList, metaList = image_buffer.getNOldestImags(N=64)

    #while img is None:
        #img, meta_data = image_buffer.getNewestImage()
    #else:
        #ts = meta_data.pop("timestamp_us")

    start0 = time()
    images, meta_data = image_buffer.getNOldestImags(N=32)
    images = tf.cast(images,tf.float32)
    print("load",time()-start0)
    #model(images)
    pred = model.predict(images)
    start1 = time()
    #pred = model(images)[0].numpy()
    all_data = predict(model, images, th=thresholdOpt, downsamples=downsamples, anchorOverlap=anchorOverlap)
    #predict()
    print("pred",time()-start1)
    print("images per second:",len(images)/(time()-start0))
    timestamps = np.array([t['timestamp_us'] for t in meta_data])

    ind = all_data[:,-1].astype(np.uint8)
    timestamps_with_detections = timestamps[ind]
    all_data_out = np.concatenate((all_data,timestamps_with_detections.reshape(len(timestamps_with_detections),1)),axis=1) #nx6 nx1
    print('WRITE TO DB', all_data_out.shape)
    write_ellipses(db_file, all_data_out)

    #assign ids if multiple cells appear on one timestamp


    #if len(all_data) != 0:
    #    slots = np.arange(slots[-1]+1,slots[-1]+1+len(all_data))
    #    slots = slots % len(outmap.rbf)
    #    print('SLOTS',slots)
    #    for i,slot in enumerate(slots):
    #        outmap.rbf[slot].data[:, ] = all_data[i, ...]
    #        outmap.rbf[slot].time_us[:,] = timestamps[ind][i]

    #slots = (slot + len(all_data_out)) % len(outmap.rbf)
    #print(slot)

    #for i in range(len(all_data_out)):
    #    outmap.rbf[slot].data[:,] = all_data_out[slot,...]


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

