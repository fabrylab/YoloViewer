from flask import Flask,render_template, Response, request, jsonify
import time
import numpy as np
from PIL import Image
from io import BytesIO
from helper_functions import ImageBuffer
import configparser
import sys
from includes.MemMap import MemMap
from record import rec
from sql_helper import fetch_larger_t0, fetch_last_3_ellipses
import pandas as pd
import json
from bg_task_checker import check_tasks
import cv2

app = Flask(__name__)
#read config
config = configparser.ConfigParser()
config.read("cfg/config.txt")

output_mmap = config["camera"]["output_mmap"]
settings_mmap = config["camera"]["settings_mmap"]
smap = MemMap(settings_mmap)
db_file = r'C:\Software\YoloViewer\database\detections.db'

columns = {'timestamp', 'frame', 'x', 'y', 'w', 'h', 'p', 'angle', 'long_axis', 'short_axis', 'radial_position',
           'measured_velocity', 'cell_id',
           'stress', 'strain', 'area', 'pressure', 'vel_fit_error', 'vel', 'vel_grad', 'eta', 'eta0', 'delta',
           'tau', 'omega', 'Gp1', 'Gp2', 'k', 'alpha'}
data = {}
variables = ['framerate', 'duration', 'save_path', 'pressure', 'imaging_position', 'aperture', 'bioink',
                     'cell_type', 'cell_passage_nr', 'time_after_harvest', 'treatment', 'room_temperature']
for v in variables:
    var = smap.__getattr__(v)
    if isinstance(var, (bytes, bytearray)):
        var = var.decode('UTF-8')
    data[f'{v}'] = str(var)

data_config={}
variables_config = ['objective', 'na', 'coupler']
for v in variables_config:
    var = config['microscope'][v]
    data_config[f'{v}'] = str(var)

# init of memmap using xml file containg the structure of the mmap file
image_buffer = ImageBuffer(output_mmap)
def gen(camera,quality=95):

    while True:
        # frame, dimension = camera.get_frame(
        #get_frame from image buffer which is memorymap located in cfg

        frame = camera.get_frame()
        if frame is None:
            #print('sleeping', file=sys.stderr)
            time.sleep(0.1)
        else:
            #print('getFrame', file=sys.stderr)
            frame = Image.fromarray(frame.squeeze(), 'L')
            buffered = BytesIO()
            #save image to a string in memory
            #https: // pillow.readthedocs.io / en / stable / reference / Image.html
            #https: // pillow.readthedocs.io / en / stable / handbook / image - file - formats.html
            frame.save(buffered, format='JPEG', quality=quality)
            frame = np.array(buffered.getvalue()).tobytes() #?
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/', methods=['POST', 'GET'])
@app.route('/index', methods=['POST', 'GET'])
def index():
        return render_template('index-1.html',data=data, columns=columns, data_config=data_config)

@app.route('/video_feed')
def video_feed():
    return Response(gen(image_buffer),mimetype='multipart/x-mixed-replace; boundary=frame')
#TODO record is executed at start of pylonFlask
@app.route('/record')
def record():
    print('RECORDING',file=sys.stderr)
    rec()
    return ""

@app.route('/set_t0')
def set_t0():
    # smap.t0 = time.time()*1e6 #eine Zehnerpotenz zu viel !?
    smap.t0 = time.time() * 1e7
    return ""

#transform data from sql-database in dataframe
def get_data_from_db_and_transform_to_df(db_file):
    t0 = smap.t0/10
    # t0 = smap.t0/10
    sql_query = fetch_larger_t0(db_file, t0)
    # print(sql_query)
    columns = ['timestamp', 'frame', 'x', 'y', 'w', 'h', 'p', 'angle', 'long_axis', 'short_axis', 'radial_position',
               'measured_velocity', 'cell_id',
               'stress', 'strain', 'area', 'pressure', 'vel_fit_error', 'vel', 'vel_grad', 'eta', 'eta0', 'delta',
               'tau', 'omega', 'Gp1', 'Gp2', 'k', 'alpha']
    df = pd.DataFrame(sql_query, columns=columns)
    # print(df)
    return df

def transform_df_to_json(df):
    result = df.to_json(orient="split", path_or_buf="mytest.json")
    return ""

#currently not used, but working
@app.route('/importJSON')
def exportJSON():
    print('SAVING JSON', file=sys.stderr)
    working = get_data_from_db_and_transform_to_df(db_file)
    # working = transform_df_to_json(working)
    transform_df_to_json(working)
    # save_json(working)
    return ""

#Create the receiver API POST endpoint; working and used
@app.route("/receiver")
def postME():
   int_val = get_data_from_db_and_transform_to_df(db_file)
   int_val = int_val.to_json()
   return jsonify(int_val)

@app.route("/camera")
def camera_output():
   gain = smap.gain
   framerate = smap.framerate
   duration = smap.duration
   data = {'gain': [gain], 'framerate': [framerate], 'duration': [duration]}
   data = pd.DataFrame(data, columns=['gain', 'framerate', 'duration'])
   data = data.to_json()
   return jsonify(data)


@app.route("/light")
def light():
    tasks = check_tasks()
    data = {'streamAcquisitionDummy2': [tasks[0]], 'mechanical': [tasks[1]], 'detect': [tasks[2]], 'pylonFlask': [tasks[3]]}
    data = pd.DataFrame(data, columns=['streamAcquisitionDummy2', 'mechanical', 'detect', 'pylonFlask'])
    data = data.to_json()
    return jsonify(data)

@app.route("/save", methods=['POST'])
def save_path():
    output = request.get_json() # this is the output that was stored in the JSON within the browser
    result = json.loads(output) # this converts the json output to a python dictionary
    smap.save_path = result['save_path']
    # print(smap.save_path.decode('UTF-8'))
    return ""

@app.route("/settings_to_map", methods=['POST'])
def to_map():
    output = request.get_json() # this is the output that was stored in the JSON within the browser
    result = json.loads(output) # this converts the json output to a python dictionary
    print(result)
    data = {}
    variables = ['framerate', 'duration', 'save_path', 'pressure', 'imaging_position', 'aperture', 'bioink',
                     'cell_type', 'cell_passage_nr', 'time_after_harvest', 'treatment', 'room_temperature']
    for index, item in enumerate(result):
        var = item
        name = variables[index]
        data[f'{name}'] = str(var)
    try:
        for k in data:
            smap.__setattr__(k, data[k])
    except:
        return 'There was an issue updating the settings'
    # print(smap.save_path.decode('UTF-8'))
    return ""

@app.route("/settings_from_map")
def from_map():
    data = {}
    variables = ['framerate', 'duration', 'save_path', 'pressure', 'imaging_position', 'aperture', 'bioink',
                     'cell_type', 'cell_passage_nr', 'time_after_harvest', 'treatment', 'room_temperature']
    for v in variables:
        var = smap.__getattr__(v)
        if isinstance(var, (bytes, bytearray)):
            var = var.decode('UTF-8')
        data[f'{v}'] = str(var)
    data = pd.DataFrame(data, columns=['framerate', 'duration', 'save_path', 'pressure', 'imaging_position', 'aperture', 'bioink',
                     'cell_type', 'cell_passage_nr', 'time_after_harvest', 'treatment', 'room_temperature'], index=[0])
    data = data.to_json()
    return jsonify(data)

@app.route('/picture')
def picture():
    def new_single():
        frame = None
        if camera_thread.image_buffer:
            frame = camera_thread.image_buffer.pop(0)
        return frame
    return Response(new_single(), mimetype='image/JPEG')

#not used atm
@app.route('/overlay')
def overlay():
    sql_query = fetch_last_3_ellipses(db_file)
    columns = ['timestamp', 'frame', 'x', 'y', 'w', 'h', 'p']
    df = pd.DataFrame(sql_query, columns=columns)
    int_val = df.to_json()
    return jsonify(int_val)

#WIP starting here, working so far
def background(number, quality= 95):
    sql_query = fetch_last_3_ellipses(db_file)
    columns = ['timestamp', 'frame', 'x', 'y', 'w', 'h', 'p']
    df = pd.DataFrame(sql_query, columns=columns)
    camera = image_buffer
    frame = camera.get_specific(timestamp=df.timestamp[number])
    # CARE currently artificial timestamp, not the correct one
    # frame = Image.fromarray(frame.squeeze(), 'L')
    # # PIL image here
    # buffered = BytesIO()
    # frame.save(buffered, format='JPEG', quality=quality)
    # frame = np.array(buffered.getvalue()).tobytes()
    # return Response(frame, mimetype='multipart/form-data, boundary=AaB03x')
    return frame, df

def overlay_ellipse(frame, df, number):
    # ['timestamp', 'frame', 'x', 'y', 'w', 'h', 'p']
    image = np.array(frame)
    # Ellipse properties
    # center_x, center_y = 250, 350
    center_x, center_y = df.x[number], df.y[number]
    a, b = df.w[number]/2, df.h[number]/2
    theta = np.deg2rad(df.p[number]) #TODO see which one is correct
    #theta = df.p[number]
    # Create x and y coordinates for grid of points
    x_samples = np.linspace(0, image.shape[1] - 1, image.shape[1])
    y_samples = np.linspace(0, image.shape[0] - 1, image.shape[0])
    x, y = np.meshgrid(x_samples, y_samples)
    thickness = 3
    # Create binary mask of ellipse using equation of an ellipse
    mask_outter = ((np.cos(theta) * (x - center_x) + np.sin(theta) * (y - center_y)) ** 2) / a ** 2 + (
                (np.sin(theta) * (x - center_x) - np.cos(theta) * (y - center_y)) ** 2) / b ** 2 <= 1

    mask_inner = ((np.cos(theta) * (x - center_x) + np.sin(theta) * (y - center_y)) ** 2) / (a - thickness) ** 2 + (
                (np.sin(theta) * (x - center_x) - np.cos(theta) * (y - center_y)) ** 2) / (b - thickness) ** 2 >= 1
    mask = np.logical_and(mask_outter, mask_inner)
    # Create a copy of the image
    overlay = image.copy()
    # Convert to 3-channel color image
    overlay = cv2.cvtColor(overlay, cv2.COLOR_GRAY2BGR)
    # Set all pixels in the overlay outside the mask to 0 (black)
    # overlay[~mask] = 0
    # Set all pixels in the overlay outside the mask to a color
    color = (0, 0, 255) # red color
    overlay[~mask] = color
    print(np.shape(overlay), 'shape overlay')
    # image = cv2.resize(image, (overlay.shape[1], overlay.shape[0]), interpolation=cv2.INTER_CUBIC)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    print(np.shape(image))
    # Use alpha blending to overlay the image with the mask
    alpha = 0.5
    overlay = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
    crop = 30
    # print(center_x,center_y,'crop',int(center_x)-crop,int(center_x)+crop,int(center_y)-crop,int(center_y)+crop)
    overlay = overlay[int(center_y)-crop:int(center_y)+crop,int(center_x)-crop:int(center_x)+crop]
    # print(overlay.shape,'shape overlay')
    # return overlay
    new_width = 90
    new_height = 90
    return cv2.resize(overlay, (new_width, new_height), interpolation = cv2.INTER_CUBIC)


@app.route('/background1')
def background1():
    frame, df = background(0) # working
    frame = overlay_ellipse(frame, df, 0)
    img = Image.fromarray(frame)
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0) #working
    return Response(img_bytes, mimetype='image/JPEG')

@app.route('/background2')
def background2():
    frame, df = background(1) # working
    frame = overlay_ellipse(frame, df, 1)
    img = Image.fromarray(frame)
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0) #working
    return Response(img_bytes, mimetype='image/JPEG')

@app.route('/background3')
def background3():
    frame, df = background(2) # working
    frame = overlay_ellipse(frame, df, 2)
    img = Image.fromarray(frame)
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0) #working
    return Response(img_bytes, mimetype='image/JPEG')



# @app.route('/background2')
# def background2():
#     frame, df = background(1)
#     return Response(frame, mimetype='image/JPEG')
# @app.route('/background3')
# def background():
#     frame, df = background(2)
#     return Response(frame, mimetype='image/JPEG')
# <!--    <img src="{{ url_for('background2') }}" class="overlay_flex_item">-->
# <!--    <img src="{{ url_for('background3') }}" class="overlay_flex_item">-->

from threading import Thread

class CameraThread(Thread):
    def __init__(self):
        super(CameraThread, self).__init__()
        self.image_buffer = []

    def run(self):
        while True:
            camera = image_buffer
            frame = camera.get_frame()
            if frame is not None:
                image = Image.fromarray(frame.squeeze(), 'L')
                buffered = BytesIO()
                image.save(buffered, format='JPEG', quality=95)
                image = np.array(buffered.getvalue()).tobytes()
                self.image_buffer.append(image)
            time.sleep(0.1)

camera_thread = CameraThread()
camera_thread.start()

if __name__ == '__main__':
    app.run(debug=True)
