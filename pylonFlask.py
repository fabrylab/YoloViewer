from flask import Flask,render_template, Response, request, jsonify, send_file
import time
import numpy as np
from PIL import Image, ImageDraw
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
variables = ['framerate', 'duration', 'pressure', 'aperture', 'imaging_position', 'bioink', 'room_temperature',
             'cell_type', 'cell_passage_nr', 'time_after_harvest', 'treatment']
for v in variables:
    var = smap.__getattr__(v)
    if isinstance(var, (bytes, bytearray)):
        var = var.decode('UTF-8')
    data[f'{v}'] = str(var)

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
        return render_template('index.html',data=data, columns=columns)

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
    data = {}
    variables = ['framerate', 'duration', 'pressure', 'aperture', 'imaging_position', 'bioink', 'room_temperature',
                     'cell_type', 'cell_passage_nr', 'time_after_harvest', 'treatment']
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
    variables = ['framerate', 'duration', 'pressure', 'aperture', 'imaging_position', 'bioink', 'room_temperature',
                     'cell_type', 'cell_passage_nr', 'time_after_harvest', 'treatment']
    for v in variables:
        var = smap.__getattr__(v)
        if isinstance(var, (bytes, bytearray)):
            var = var.decode('UTF-8')
        data[f'{v}'] = str(var)
    data = pd.DataFrame(data, columns=['framerate', 'duration', 'pressure', 'aperture', 'imaging_position', 'bioink', 'room_temperature',
                     'cell_type', 'cell_passage_nr', 'time_after_harvest', 'treatment'], index=[0])
    data = data.to_json()
    return jsonify(data)

@app.route('/picture')
def picture():
    def new_single():
        if camera_thread.image_buffer:
            frame = camera_thread.image_buffer.pop(0)
        return frame
    return Response(new_single(), mimetype='image/JPEG')

#yolo output overlay; working -> json data is on webpage
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
    # timestamp_example = df.timestamp[0]
    # print(timestamp_example)
    camera = image_buffer
    frame = camera.get_specific(timestamp=df.timestamp[number])
    # CARE currently artificial timestamp, not the correct one
    frame = Image.fromarray(frame.squeeze(), 'L')
    # # PIL image here
    # buffered = BytesIO()
    # frame.save(buffered, format='JPEG', quality=quality)
    # frame = np.array(buffered.getvalue()).tobytes()
    # return Response(frame, mimetype='multipart/form-data, boundary=AaB03x')
    print(type(frame))
    return frame, df

# not working so far
def overlay_ellipse(frame, df):
    quality = 95
    # Load the image
    img = cv2.imread("static/images/Test.png")
    # Get the ellipse parameters
    center = (100, 100)
    axes = (50, 30)
    angle = 45
    # Overlay the ellipse on the image
    cv2.ellipse(img, center, axes, angle, 0, 360, (255, 0, 0), 2)
    img = Image.fromarray(img)
    print(type(img))
    return img

@app.route('/background1')
def background1():
    frame, df = background(0)
    # print(frame, df)
    frame = overlay_ellipse(frame, df)
    # return Response(frame.getvalue(), content_type='image/jpeg')
    # return Response(frame, mimetype='image/JPEG')
    # return frame
    return send_file(frame, mimetype='image/JPEG')


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
    app.run(host='0.0.0.0', debug=True, threaded=True)
