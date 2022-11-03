#!/usr/bin/python3.6
import os
os.environ["OPENBLAS_CORETYPE"] = "ARMV8"
import tifffile
from helper_functions import ImageBuffer, write_config
from sql_helper import *
from mechanical_helper import calculate_mech_prop
import os
import time
import signal
from datetime import datetime, timedelta
import numpy as np
from PIL import Image
import configparser
from includes.MemMap import MemMap
import configparser
import clickpoints
from clickpoints.DataFile import packToDictList
import pandas as pd

def rec():
    start_time = datetime.now()

    config = configparser.ConfigParser()
    config.read("cfg/config.txt")

    output_mmap = config["camera"]["output_mmap"]
    settings_mmap = config["camera"]["settings_mmap"]
    #yolo_output_mmap = config["camera"]["yolo_output_mmap"]

    smap = MemMap(settings_mmap)
    #outmap = MemMap(yolo_output_mmap)

    image_buffer = ImageBuffer(output_mmap)

    framerate = smap.framerate
    duration = smap.duration
    save_path = smap.save_path
    save_path = r'C:\Software\YoloViewer'


    sleeptime = 1/framerate


    if not os.path.exists(save_path):
        os.makedirs(save_path)
    tif_name = str(start_time.year) + '_' + \
               '{0:02d}'.format(start_time.month) + '_' + \
               '{0:02d}'.format(start_time.day) + '_' + \
               '{0:02d}'.format(start_time.hour) + '_' + \
               '{0:02d}'.format(start_time.minute) + '_' + \
               '{0:02d}'.format(start_time.second)

    tif_path = os.path.join(save_path, f"{tif_name}.tif")
    cdb_file = os.path.join(save_path, f"{tif_name}.cdb")
    csv_file = os.path.join(save_path, f"{tif_name}.csv")

    #smap.start_time = tif_name

    tiffWriter = tifffile.TiffWriter(tif_path, bigtiff=True)

    timestamps = []

    #all_detections = []
    rec_start = time.time()
    while time.time()-rec_start < duration:
        img = None
        meta_data = {}
        tstart = datetime.now()
        while img is None:
            img, meta_data = image_buffer.getNewestImage()
        else:
            ts = meta_data["timestamp_us"]
            timestamps.append(int(ts))
            #TODO compress images with jpg
            # parser.add_argument("--quality", help="jpeg quality", type=int, default=95)
            #if camInfo["output_file_format"].lower() == ".jpg" and dtype.itemsize > 1:
            #    q1 = np.percentile(img, 1)
            #    q99 = np.percentile(img, 99)
            #    img = (img - q1) * (255 / (q99 - q1))
            #    img[img < 0] = 0
            #    img[img > 255] = 255
            #    img = img.astype(np.uint8)

            # save image

            compression =0 #"jpeg" 0.005s, compression:0 0.001, 4:
            tiffWriter.save(img, compression=compression, metadata=meta_data, contiguous=False)


            #all_data = []
            #ts_detections = []

            #for slot in range(len(outmap.rbf)):
            #    d = outmap.rbf[slot].data
            #    ts_det = outmap.rbf[slot].time_us
            #    all_data.append(d)
            #    ts_detections.append(ts_det)

            #all_data = np.array(all_data)
            #ts_detections = np.array(ts_detections)
#
            #correct the imageID from batch to global tiff stack
            #ts_recording = np.array(timestamps)
            #ind = np.argwhere(np.isin(ts_recording, ts_detections)).ravel()
#
            #mask = np.isin(ts_detections, ts_recording).ravel()
            #print('IND',ind)
            # all_data = all_data[all_data[:, -1] < N]
            #all_detections.append(all_data[mask])

            timeUsed = (datetime.now()-tstart).total_seconds()
            time.sleep(max(0, (sleeptime-timeUsed-0.01)))
            timeUsed = (datetime.now()-tstart).total_seconds()
            print(tif_path, "fps:%.2f"%(1./timeUsed), "/%.2f"%(framerate))
    tiffWriter.close()

    #get data from database
    db_file = r'C:\Software\YoloViewer\database\detections.db'
    df = fetch_larger_t0(db_file,rec_start*1e6)
    columns = ['timestamp', 'frame', 'x', 'y', 'w', 'h', 'p', 'angle', 'long_axis', 'short_axis', 'radial_position',
               'measured_velocity', 'cell_id',
               'stress', 'strain', 'area', 'pressure', 'vel_fit_error', 'vel', 'vel_grad', 'eta', 'eta0', 'delta',
               'tau', 'omega', 'Gp1', 'Gp2', 'k', 'alpha']

    df = pd.DataFrame(df, columns=columns)
    arr = np.array(df)
    # write ellipses

    with clickpoints.DataFile(cdb_file, "w") as cdb:
        cdb._SQLITE_MAX_VARIABLE_NUMBER = 99999 # speeds up creation of databases enormously
        cdbPath = cdb.setPath(".")
        im = cdb.setImage(filename=tif_path, path=cdbPath)
        N = len(timestamps)
        data = packToDictList(cdb.table_image,
                              filename=tif_path,
                              ext=os.path.splitext(tif_path)[1],
                              frame=list(range(N)),
                              path=cdbPath,
                              layer=im.layer,
                              sort_index=list(range(N)),
                              )
        cdb.saveReplaceMany(cdb.table_image, data)

        mtype = cdb.setMarkerType(mode=cdb.TYPE_Ellipse, color="#FF8800", name="ellipse")
        timestamps = np.array(timestamps)

        ts_detection = np.array(df['timestamp'])
        frames = np.argwhere(np.isin(timestamps, ts_detection)).ravel()
        angle = np.where(arr[:,6]>90.,arr[:,6]-180.,arr[:,6])

        cdb.setEllipses(x=np.array(arr[:,2]), y=arr[:,3], width=arr[:,4],
                        height=arr[:,5], angle=angle,
                        frame=list(frames.astype(int)),
                        type=mtype  # ,[f'{i}' for i in c.T[~np.any(NM, axis=1)]])
                        )

    #to csv
    df.to_csv(csv_file)


    config_path = os.path.join(save_path, f"{tif_name}_config.txt")
    write_config(config_path,smap)

rec()