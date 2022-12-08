import sqlite3
import configparser
from includes.MemMap import MemMap
from sql_helper import *
from helper_functions import create_config
import pandas as pd
from mechanical_helper import *
import signal
import time

cfg = configparser.ConfigParser()
cfg.read("cfg/config.txt")

settings_mmap = cfg["camera"]["settings_mmap"]
smap = MemMap(settings_mmap)


#get t0
t0 = smap.t0/10
print(smap.t0)
print(t0)
#1669198039

db_file = r'C:\Software\YoloViewer\database\detections.db'
# setup ctrl + c handler

run = True
def signal_handler(sig, frame):
    global run  # we need to have this as global to work
    print("Ctrl+C received")
    print("Shutting down Detector ...")
    run = False
signal.signal(signal.SIGINT, signal_handler)

while run:
    starting = time.time()
    config = create_config(smap,cfg)
    all_data = np.array((fetch_ellipses_larger_t0(db_file, t0)))
    df = pd.DataFrame(all_data,columns=['timestamp','frame','x', 'y', 'w', 'h', 'p'])

    df = transform_angle(df)

    # calculate long and short axes from w,h
    #magnification = float(config['microscope']['objective'].split()[0])
    #coupler = float(config['microscope']['coupler'].split()[0])
    #camera_pixel_size = float(config['camera']['camera pixel size'].split()[0])
    #pixel_size = camera_pixel_size / (magnification * coupler) # in u meter
    #channel_width_px = float(config['setup']['channel width'].split()[0]) / pixel_size # in pixels

    df['long_axis'] = df['w'] * config["pixel_size"]
    df['short_axis'] = df['h'] * config["pixel_size"]

    # add radial position
    df['radial_position'] = (df['y'] - config["channel_width_px"] / 2) * config["pixel_size"]
    df['measured_velocity'] = np.zeros(len(df))
    df['cell_id'] = np.arange(len(df))

    cells = []
    for i in range(len(df.frame) - 1):
        t0, t1 = int(df['frame'][i]), int(df['frame'][i + 1])

        new_cells = matchVelocities(df.iloc[i:i + 1], df.iloc[i + 1:i + 2], config)

    df['measured_velocity'][df['measured_velocity'] == 0] = np.nan

    # correct center
    df = correctCenter(df, config)

    # get Stress Strain
    getStressStrain(df, config)

    df["area"] = df.long_axis * df.short_axis * np.pi
    df["pressure"] = float(smap.pressure) * 1e-5

    df, p = improved_fit(df, plot=False)

    try:
        match_cells_from_all_data(df, config, 720)
    except AttributeError as err:
        print("Err", err)

    mask_ls = df["long_axis"] > df["short_axis"]
    df = df[mask_ls]

    get_cell_properties(df)

    #write to db
    #df.to_csv(r'\\131.188.117.96\biophysDS2\jbartl\del-me.csv')
    write_mechanical(db_file,df)
    print(time.time()-starting)