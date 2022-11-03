import clickpoints
from includes.MemMap import MemMap
import configparser
from clickpoints.DataFile import packToDictList
import os
import signal
import numpy as np
#read config
config = configparser.ConfigParser()
config.read("cfg/config.txt")

settings_mmap = config["camera"]["settings_mmap"]
yolo_output_mmap = config["camera"]["yolo_output_mmap"]

smap = MemMap(settings_mmap)
outmap = MemMap(yolo_output_mmap)


start_time = smap.start_time
start_time = '2022_10_12_16_49_57'
save_path = smap.save_path
save_path = r'C:\Software\YoloViewer'#TODO write save_path into smap from gui
#TODO Can i write str to mmamp?


cdb_file = os.path.join(save_path,f"{start_time}.cdb")
tif_file = os.path.join(save_path,f"{start_time}.tif")

with clickpoints.DataFile(cdb_file, "w") as cdb:
    # cdb._SQLITE_MAX_VARIABLE_NUMBER = 99999 # speeds up creation of databases enormously
    cdbPath = cdb.setPath(".")
    im = cdb.setImage(filename=tif_file, path=cdbPath)
    N = 20000
    data = packToDictList(cdb.table_image,
                          filename=tif_file,
                          ext=os.path.splitext(tif_file)[1],
                          frame=list(range(N)),
                          path=cdbPath,
                          layer=im.layer,
                          sort_index=list(range(N)),
                          )
    cdb.saveReplaceMany(cdb.table_image, data)

run = True
def signal_handler(sig, frame):
    global run  # we need to have this as global to work
    print("Ctrl+C received")
    print("Shutting down Detector ...")
    run = False
signal.signal(signal.SIGINT, signal_handler)

while run:
    mtype = cdb.setMarkerType(mode=cdb.TYPE_Ellipse, color="#FF8800", name="ellipse")
    all_data = []
    for slot in range(len(outmap.rbf)):
        d = outmap.rbf[slot].data
        all_data.append(d)

    all_data = np.array(all_data)
    print(all_data[0])

    #all_data = all_data[all_data[:, -1] < N]
    cdb.setEllipses(x=all_data[:, 0], y=all_data[:, 1], width=all_data[:, 2], height=all_data[:, 3],
                    angle=all_data[:, 4],
                    frame=list(all_data[:, 5].astype(int)),
                    type=mtype  # ,[f'{i}' for i in c.T[~np.any(NM, axis=1)]])
                    )
    break