from flask import Flask,render_template, Response, request,redirect, jsonify
import time
import numpy as np
from PIL import Image
from io import BytesIO
from helper_functions import ImageBuffer
import configparser
import sys
from includes.MemMap import MemMap
from record import rec
from sql_helper import fetch_larger_t0
import pandas as pd
import json
from bg_task_checker import check_tasks

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
    data = {}
    variables = ["framerate", "duration", "pressure", "aperture", "imaging_position", "bioink", "room_temperature",
                 "cell_type", "cell_passage_nr", "time_after_harvest", "treatment"]
    if request.method == 'POST':

        for v in variables:
            data[v] = request.form[v]
        print(data)


        try:
            for k in data:
                smap.__setattr__(k,data[k])

            redirect_str = "/index?"
            for k in data:
                redirect_str += f"{k}={data[k]}&"
            return redirect(redirect_str)
            #return redirect(f"/index?framerate={new_framerate}&duration={new_duration}&pressure={new_pressure}&aperture={new_aperture}&imaging_position={new_imaging_position}&bioink={new_bioink}&room_temperature={new_room_temperature}&cell_type={new_cell_type}&cell_passage_nr={new_cell_passage_nr}&time_after_harvest={new_time_after_harvest}&treatment={new_treatment}")
        except:
            return 'There was an issue updating the framerate'

    else:


        for v in variables:
            var = request.args.get(v)
            #print(var, file=sys.stderr)
            if var == None:
                var = smap.__getattr__(v)
                if isinstance(var, (bytes, bytearray)):
                    var = var.decode('UTF-8')

            data[v] = var
        print('data',data,file=sys.stderr)

        #df = pd.DataFrame({
        #    'Fruit': ['Apples', 'Oranges', 'Bananas', 'Apples', 'Oranges',
        #              'Bananas'],
        #    'Amount': [4, 1, 2, 2, 4, 5],
        #    'City': ['SF', 'SF', 'SF', 'Montreal', 'Montreal', 'Montreal']
        #})
        #fig = px.bar(df, x='Fruit', y='Amount', color='City',
        #             barmode='group')
        #graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template('index.html',data=data, columns=columns)#,graphJSON = graphJSON)


#https://flask.palletsprojects.com/en/2.0.x/patterns/streaming/
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


#not working; pause button
# @app.route('/is_decoded/')
# def is_decoded():
#     camera = image_buffer
#     return jsonify({'is_decoded': camera.is_decoded})


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True)
