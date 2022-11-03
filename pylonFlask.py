from flask import Flask,render_template, Response, request,redirect
import time
import numpy as np
from PIL import Image
from io import BytesIO
from helper_functions import ImageBuffer
import configparser
import sys
from includes.MemMap import MemMap
from record import rec
import plotly
import plotly.express as px
import pandas as pd
app = Flask(__name__)
import json


#read config
config = configparser.ConfigParser()
config.read("cfg/config.txt")

output_mmap = config["camera"]["output_mmap"]
settings_mmap = config["camera"]["settings_mmap"]
smap = MemMap(settings_mmap)


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

        return render_template('index.html',data=data)#,graphJSON = graphJSON)


#https://flask.palletsprojects.com/en/2.0.x/patterns/streaming/
@app.route('/video_feed')
def video_feed():
    return Response(gen(image_buffer),mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/record', methods=['POST', 'GET'])
def record():
    print('RECORDING',file=sys.stderr)
    rec()
    return ""


def set_t0():
    smap.start_time = time.time()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

