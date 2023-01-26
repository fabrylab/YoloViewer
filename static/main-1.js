
const image = document.getElementById("bright_field");
panzoom(image, {
  maxZoom: 3,
  minZoom: 1,

});
const image2 = document.getElementById("fluorescence");
const panzoom1 = panzoom(image2, {
    maxZoom: 3,
    minZoom: 1,
    bounds: { left: 0, right: 720, top: 0, bottom: 540 }
});

window.addEventListener("keydown", function(event) {
  if (event.code === "KeyF") {
    document.getElementById("experiment_parameter").style.backgroundColor = "green";
    panzoom1.reset();
  }
});

/* Plots */
var layout = {
    margin: {
        t: 40,
        r: 60,
        b: 40,
        l: 50
    },
    xaxis: {
        linewidth: 1,
        mirror: true
    },
    yaxis: {
        linewidth: 1,
        mirror: true
    },
    showlegend: false,

};
config = {
    displayModeBar: false,
    displaylogo: false,
    responsive:true,
}
//first graph:velocity over position
var data_pos_vel = [{
    x: [6,4,3,1],
    y: [1,2.5,2.7,3],
    mode: 'markers',
    type: 'scatter',
    name: 'data',
}];

var data_fit_pos_vel = {
    x: [6,4,3,1],
    y: [1,2.5,2.7,3],
    type: 'scatter',
    mode: 'lines',
    line: {color: 'black'},
    name: 'fit',

};

var layout_pos_vel = {...layout};
var layout_stress_strain = {...layout};

layout_stress_strain.xaxis.title = "position in channel (µm)";
layout_stress_strain.yaxis.title = "velocity (cm/s)";

layout_pos_vel.annotations = [{
        xref: 'paper',
        yref: 'paper',
        x: 0.1,
        y: 0.2,
        text: "\u03B7\u2080: X.XX<br>\u03B4: X.XX<br>\u03C4: X.XX",
        showarrow: false,
  }],
Plotly.newPlot('plot_vel_profile', data_pos_vel, layout_pos_vel, config);
Plotly.addTraces('plot_vel_profile', data_fit_pos_vel);
//Plotly.newPlot('plot_vel_profile', data_fit_pos_vel, layout_pos_vel,config);
//second graph:strain over stress
var data_scatter = [{
    mode: 'markers',
    marker: {
        //size: 10,
        colorscale: 'Viridis'
    }
}];

var data_stress_strain = data_scatter.slice();
data_stress_strain[0].x = [5, 5, 5, 5, 5, 5, 5, 6, 7, 8, 9, 10, 11, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5];
data_stress_strain[0].y = [6, 2, 3, 4, 5, 6, 7, 8, 12, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5];
data_stress_strain[0].marker.color = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39];

var layout_stress_strain = {...layout};
layout_stress_strain.xaxis.title = "strain";
layout_stress_strain.yaxis.title = "stress [Pa]"

Plotly.newPlot('plot_stress_strain', data_stress_strain, layout_stress_strain, config);

//third graph:angle over rp
var layout_angle_rp = {...layout};
layout_angle_rp.xaxis.title = "radial position [µm]";
layout_angle_rp.yaxis.title = "angle [deg]"

var data_angle_rp = data_scatter.slice();
data_stress_strain[0].x = [5, 5, 5];
data_stress_strain[0].y = [6, 2, 3];
data_stress_strain[0].marker.color = [0, 1, 2];

Plotly.newPlot('plot_angle_rp', data_angle_rp, layout_angle_rp, config);

//fourth plot: g_g
var layout_g_g = {...layout};
layout_g_g.xaxis.title = "angular frequency";
layout_g_g.yaxis.title = "G'/G''";



// create the first trace
var g_prime = {
    x: [1, 2, 3, 4, 5],
    y: [5, 2, 3, 4, 5],
    mode: 'markers',
    marker: {
        color: 'b',
        //size: 10
    },
    type: 'scatter',
    name: "G'"
};

// create the second trace
var g_double_prime = {
    x: [1, 2, 3, 4, 5],
    y: [1, 4, 2, 3, 5],
    mode: 'markers',
    marker: {
        color: 'o',
        //size: 10
    },
    type: 'scatter',
    name: "G''"
};

// combine the two traces
var data_g_g = [g_prime, g_double_prime];

Plotly.newPlot('plot_g_g', data_g_g, layout_g_g, config);

//fivth and final plot: k vs alpha

var data_k_alpha = data_scatter.slice();
data_k_alpha[0].x = [5, 5, 5, 5, 5, 5, 5, 6, 7, 8, 9, 10, 11, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5];
data_k_alpha[0].y = [6, 2, 3, 4, 5, 6, 7, 8, 12, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5];
data_k_alpha[0].marker.color = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39];

var layout_k_alpha = {...layout};
layout_k_alpha.xaxis.title = "stiffness k [Pa]";
layout_k_alpha.yaxis.title = "fluidity \u03B1"

layout_k_alpha.annotations = [{
        xref: 'paper',
        yref: 'paper',
        x: 0.8,
        y: 0.8,
        text: "k: X.XX<br>\u03B1: X.XX",
        showarrow: false,
  }],

Plotly.newPlot('plot_k_alpha', data_k_alpha, layout_k_alpha, config);





var clear = document.querySelector("#clear");
clear.addEventListener('click',set_t0,false);
function set_t0(){
        $.ajax({
            url:"/set_t0",
            context: document.body});
            clear_traces(0);
            };

function get_all_after_t0(){
        $.ajax({
            url:"/set_t0",
            context: document.body});
            };

var dummy = document.querySelector("#dummy");
dummy.addEventListener("click", change_dummy, false);

function change_dummy(){
   if (document.getElementById("Dummy").style.display === "none"){
        document.getElementById("Dummy").style.display = "inline";
        $('#dummy').find("i").toggleClass("fa-play fa-stop");
        $('#pause').find("i").toggleClass("fa-play fa-pause");
        }
   else {
        document.getElementById("Dummy").style.display = "none";
        $('#dummy').find("i").toggleClass("fa-stop fa-play");
        $('#pause').find("i").toggleClass("fa-pause fa-play");
   }
};


var camera_output;
function gain(){
        fetch('http://127.0.0.1:5000/camera')
        .then(response => response.json())
        .then(result => {
        camera_output = JSON.parse(result);
        })
        .then(() => {   console.log(camera_output);
                        var gain = json2array(camera_output.gain);
                        var framerate = json2array(camera_output.framerate);
                        var duration = json2array(camera_output.duration);
                        document.getElementById("show_gain").innerHTML = "gain: " + gain;
                        document.getElementById("show_framerate").innerHTML = framerate + " fps";
                        document.getElementById("show_duration").innerHTML = "duration: " + duration + " s";
        });
    setInterval(() => {
        fetch('http://127.0.0.1:5000/camera')
        .then(response => response.json())
        .then(result => {
        camera_output = JSON.parse(result);
        })
        .then(() => {   console.log(camera_output);
                        var gain = json2array(camera_output.gain);
                        var framerate = json2array(camera_output.framerate);
                        var duration = json2array(camera_output.duration);
                        document.getElementById("show_gain").innerHTML = "gain: " + gain;
                        document.getElementById("show_framerate").innerHTML = framerate + " fps";
                        document.getElementById("show_duration").innerHTML = "duration: " + duration + " s";
        })
        fetch('http://127.0.0.1:5000/light')
        .then(response => response.json())
        .then(result => {
        tasks = JSON.parse(result);
        })
        .then(() => {   console.log(tasks);
                        var streamAcquisitionDummy2 = json2array(tasks.streamAcquisitionDummy2); //second from left
                        var mechanical = json2array(tasks.mechanical); //second from right
                        var detect = json2array(tasks.detect); //first from right
                        var pylonFlask = json2array(tasks.pylonFlask); //first from left
                        if (streamAcquisitionDummy2 == "true"){
                            document.getElementById("status_light_acquisition").style.backgroundColor = "DodgerBlue";
                            }
                        else if (streamAcquisitionDummy2 == "false"){
                            document.getElementById("status_light_acquisition").style.backgroundColor = "grey";
                        }
                        if (mechanical == "true"){
                            document.getElementById("status_light_mechanical").style.backgroundColor = "DodgerBlue";
                            }
                        else if (mechanical == "false"){
                            document.getElementById("status_light_mechanical").style.backgroundColor = "grey";
                        }
                        if (detect == "true"){
                            document.getElementById("status_light_detect").style.backgroundColor = "DodgerBlue";
                            }
                        else if (detect == "false"){
                            document.getElementById("status_light_detect").style.backgroundColor = "grey";
                        }
                        if (pylonFlask == "true"){
                            document.getElementById("status_light_flask").style.backgroundColor = "DodgerBlue";
                            }
                        else if (pylonFlask == "false"){
                            document.getElementById("status_light_flask").style.backgroundColor = "grey";
                        };
        })
        var right_progress_bar = document.getElementById('pause').getBoundingClientRect().right; //style="width:875px"
        document.getElementById("progress_bar").style.width = right_progress_bar - 10 + "px";
    }, 3000);
};



var plot = document.querySelector("#plot");
plot.addEventListener("click", show_plot, false);

function interval_function(interval) {
    myVar = setInterval(() => {new_recieve()}, interval);
};

var myVar;
function show_plot(){
    document.getElementById("graph").style.display="inline";
    document.getElementById("graph2").style.display="inline";
    document.getElementById("graph3").style.display="inline";
    document.getElementById("graph4").style.display="inline";
    document.getElementById("graph5").style.display="inline";
//    document.getElementById("plot_wrapper3").style.display="inline";
    interval_function(10000);
//    clearInterval(myVar);
}

function test(){
    alert("!");
};

//resets plots
function clear_traces(trace) {
    Plotly.deleteTraces('graph', trace);
    Plotly.newPlot('graph2', 0);
    Plotly.deleteTraces('graph3', 0);
    Plotly.deleteTraces('graph4', 0);
    Plotly.deleteTraces('graph4', 1);
    Plotly.deleteTraces('graph5', 0);
    Plotly.newPlot('playground_plot', 0);
};

// function to transform json object to javascript array
function json2array(json){
    var result = [];
    var keys = Object.keys(json);
    keys.forEach(function(key){
        result.push(json[key]);
    });
    return result;
}

var obj = [];
// function to plot all plots at once in dedicated div_boxes
function new_recieve() {
        fetch('http://127.0.0.1:5000/receiver')
        .then(response => response.json())
        .then(result => {
        obj = JSON.parse(result);

        })
        .then(() => {   //first graph:strain over stress
                            var x_axis = json2array(obj.stress);
                            var y_axis = json2array(obj.strain);
                            var value1="stress in Pa";
                            var value2="strain";
                            var data = [{x: x_axis,
                                        y: y_axis,
                                        mode: 'markers',
                                        type: 'scatter'
                            }];
                            var layout = {
                                    xaxis: {range: [Math.min(x_axis), Math.max(x_axis)], title: `${value1}`},
                                    yaxis: {range: [Math.min(y_axis), Math.max(y_axis)], title: `${value2}`}
                            };
                        Plotly.newPlot('plot_vel_profile',data, layout)
                        //second graph:angle over radial_position
                            var x_axis = json2array(obj.radial_position);
                            var y_axis = json2array(obj.angle);
                            var value1="radial position in µm";
                            var value2="angle in deg";
                            var data = [{x: x_axis,
                                        y: y_axis,
                                        type: 'histogram2dcontour'
                            }];
                            var layout = {
                                xaxis: {range: [Math.min(x_axis), Math.max(x_axis)], title: `${value1}`},
                                yaxis: {range: [Math.min(y_axis), Math.max(y_axis)], title: `${value2}`}
                            };
                        Plotly.newPlot('plot_vel_profile',data, layout)
                        //third graph:velocity over position
                            var x_axis = json2array(obj.radial_position);
                            var y_axis = json2array(obj.vel);
                            var value1="position in channel (µm)";
                            var value2="velocity (cm/s)";
                            var data = [{x: x_axis,
                                        y: y_axis,
                                        mode: 'markers',
                                        type: 'scatter'
                            }];
                            var layout = {
                                    xaxis: {range: [Math.min(x_axis), Math.max(x_axis)], title: `${value1}`},
                                    yaxis: {range: [Math.min(y_axis), Math.max(y_axis)], title: `${value2}`}
                            };
                        Plotly.newPlot('graph3',data, layout)
                        //forth graph: G'/G'' over angular frequency TODO add trace 2
                            var x_axis = json2array(obj.radial_position);
                            var y_axis = json2array(obj.Gp1);
                            var y_axis2 = json2array(obj.Gp2);
                            var value1="angular frequency";
                            var value2="G'/G\"";
                            var data = [{x: x_axis,
                                        y: y_axis,
                                        name: 'G\'',
                                        mode: 'markers',
                                        type: 'scatter'
                            },{         x: x_axis,
                                        y: y_axis2,
                                        name: 'G\"',
                                        mode: 'markers',
                                        type: 'scatter'
                            }];
                            var layout = {
                                    xaxis: {range: [Math.min(x_axis), Math.max(x_axis)], title: `${value1}`,type: 'log', autorange: true},
                                    yaxis: {range: [Math.min(y_axis), Math.max(y_axis)], title: `${value2}`,type: 'log', autorange: true}
                            };
                        Plotly.newPlot('graph4',data, layout)
                        //fifth graph:fluidity alpha over stiffness
                            var x_axis = json2array(obj.k);
                            var y_axis = json2array(obj.alpha);
                            var value1="stiffness k (Pa)";
                            var value2="fluidity \u03B1";
                            var data = [{x: x_axis,
                                        y: y_axis,
                                        mode: 'markers',
                                        type: 'scatter'
                            }];
                            var layout = {
                                    xaxis: {range: [Math.min(x_axis), Math.max(x_axis)], title: `${value1}`,type: 'log', autorange: true},
                                    yaxis: {range: [Math.min(y_axis), Math.max(y_axis)], title: `${value2}`}
                            };
                        Plotly.newPlot('graph5',data, layout)
       });
};
// TODO: get this pause button working -> pause gen(ImageBuffer) in flask
var vid = document.getElementById("Dummy");
var pause_button = document.getElementById("pause");
var swap_pause_status = "on";
//pause_button.addEventListener("click", pauseVid, false);
pause_button.addEventListener("click", swap_pause, false);
if (vid.style.display="none"){
    $('#pause').find("i").toggleClass("fa-pause fa-play");
};

/*
function switch_fullscreen() {
    document.getElementById("live_view").style.backgroundColor = "red";
    document.getElementById("live_view").style.position = "fixed";
    document.getElementById("live_view").style.width("100%");
    document.getElementById("live_view").style.height("100%");
    document.getElementById("live_view").style.top("0");
    document.getElementById("live_view").style.left("0");
};
*/

function swap_pause() {
//    document.getElementById("pause").innerHTML = "Paragraph changed!";

    if (swap_pause_status === "on"){
//        $('#pause').find("i").toggleClass("fa-pause fa-play");
        swap_pause_status = "off";
        change_dummy();
        pause();
        document.getElementById("Dummy").src ="/picture";
        document.getElementById("Dummy").style.display = "inline";
    }
    else if (swap_pause_status === "off"){
//        $('#pause').find("i").toggleClass("fa-play fa-pause");
        swap_pause_status = "on";
        change_dummy();
        document.getElementById("Dummy").src ="/video_feed";
    }
};

function move() {
  var elem = document.getElementById("myBar");
  var width = 0;
  fetch('http://127.0.0.1:5000/camera')
        .then(response => response.json())
        .then(result => {
        camera_output = JSON.parse(result);
        })
        .then(() => {
            var duration = json2array(camera_output.duration);
            duration = duration[0];
            var id = setInterval(frame, (duration/100)*1000);
    function frame() {
    if (width >= 100) {
      clearInterval(id);
    } else {
      width++;
      elem.style.width = width + '%';
      elem.innerHTML = width * 1  + '%';
    }
  };
  });
}

$(function() {$("#record").click(function (event) { $.getJSON('/record', { },
    function(data) { }); return false; }); });
$(function() {$("#record").click(function (event) { move(); return false; }); });

var notes_status = "off";
var x = document.createElement("textarea");
x.style.display = "none";
function notes() {
    if (notes_status === "off"){
        x.style.position = "absolute";
        x.style.left = "320px";
        x.style.width = "545px";
        x.style.height = "230px";
        x.style.display = "inline";
        x.placeholder = "Type your notes here...";
        x.id = "notes";
        document.body.appendChild(x);
        notes_status = "on";
        document.getElementById("microscope_settings_div").style.display="none";
        document.getElementById("save_notes").style.display="inline";
        }
    else if (notes_status === "on"){
        notes_status = "off";
        document.getElementById("microscope_settings_div").style.display="inline";
        x.style.display = "none";
        document.body.appendChild(x);
        document.getElementById("save_notes").style.display="none";
    }
}


function saveTextAsFile() {
  var textToWrite = document.getElementById('notes').value;
  var textFileAsBlob = new Blob([ textToWrite ], { type: 'text/plain' });
  var fileNameToSaveAs = "notes.txt"; //filename.extension
  var downloadLink = document.createElement("a");
  downloadLink.download = fileNameToSaveAs;
  downloadLink.innerHTML = "Download File";
  if (window.webkitURL != null) {
    // Chrome allows the link to be clicked without actually adding it to the DOM.
    downloadLink.href = window.webkitURL.createObjectURL(textFileAsBlob);
  } else {
    // Firefox requires the link to be added to the DOM before it can be clicked.
    downloadLink.href = window.URL.createObjectURL(textFileAsBlob);
    downloadLink.onclick = destroyClickedElement;
    downloadLink.style.display = "none";
    document.body.appendChild(downloadLink);
  }
  downloadLink.click();
}

function destroyClickedElement(event) {// remove the link from the DOM
  document.body.removeChild(event.target);
}

//drop-down menu for playground
var plot_selector1 = document.getElementById("plot_selector_1");
var selection1 = plot_selector1.value.toString();
var plot_selector2 = document.getElementById("plot_selector_2");
var selection2 = plot_selector2.value.toString();
document.getElementById("plot_wrapper3").style.display="inline";
//document.getElementById("plot_selector_1").addEventListener("change", for_update);
//document.getElementById("plot_selector_2").addEventListener("change", for_update);
function for_update(){
    var plot_selector1 = document.getElementById("plot_selector_1");
    var selection1 = plot_selector1.value.toString();
    var plot_selector2 = document.getElementById("plot_selector_2");
    var selection2 = plot_selector2.value.toString();
    if (selection1 === "-1" || selection2 === "-1"){
        document.getElementById("update_playground").style.display="none";
    }
    else {document.getElementById("update_playground").style.display="inline";};
};
for_update();

function update(){
    document.getElementById("playground_plot").style.display="inline";
    var plot_selector1 = document.getElementById("plot_selector_1");
    var selection1 = plot_selector1.value.toString();
    var plot_selector2 = document.getElementById("plot_selector_2");
    var selection2 = plot_selector2.value.toString();
//    Plotly.newPlot('playground_plot', 0);
//    Plotly.deleteTraces('playground_plot', 0);
    playground(selection1,selection2);
};


function playground(x_sel, y_sel) {
            fetch('http://127.0.0.1:5000/receiver')
            .then(response => response.json())
            .then(result => {
            obj = JSON.parse(result);
            })
            .then(() => {
                            if (x_sel != "-1" && y_sel != "-1" ){
                                var x_axis = json2array(obj[x_sel]);
                                var y_axis = json2array(obj[y_sel]);
                                var value1= "${x_sel}";
                                var value2= "${y_sel}";
                                var data = [{x: x_axis,
                                            y: y_axis,
                                            mode: 'markers',
                                            type: 'scatter'
                                }];
                            }
                            else {
                                alert("Error");
                            }
                            var layout = {
                                    xaxis: {range: [Math.min(x_axis), Math.max(x_axis)], title: `${x_sel}`},
                                    yaxis: {range: [Math.min(y_axis), Math.max(y_axis)], title: `${y_sel}`}
                            };
                            Plotly.newPlot('playground_plot',data, layout);
           });
};

var save_path;
function pop() {
     save_path = prompt(`Please enter your desired save path.
If you do not want to write it by hand:
     first: open the explorer
     second: navigate to the desired directory
     third: left click in the address bar left of refresh (circular arrow)
     last: copy/paste the marked path to this window`, `C:\\Software\\YoloViewer\\example`);
     console.log(save_path);
        const dict_values = {save_path} //Pass the javascript variables to a dictionary.
        var s = JSON.stringify(dict_values); // Stringify converts a JavaScript object or value to a JSON string
//        s = s.replace(String.fromCharCode(92,92),String.fromCharCode(92));
        console.log(s);
            $.ajax({
            url:"/save",
            type:"POST",
            contentType: "application/json",
            data: JSON.stringify(s)});
};

// Please add a second backslash(on keyboard:alt gr + ? or copy this: \\)to each backslash

// new settings
function settings() {
            fetch('http://127.0.0.1:5000/settings_from_map')
            .then(response => response.json())
            .then(result => {
            obj = JSON.parse(result);
            })
            .then(() => {
                console.log(obj);
                Object.entries(obj).forEach(
//                ([key, value]) => console.log(key, value));
                ([key, value]) => document.getElementById(`settings_${key}`).placeholder = `${value[0]}`);
           });
};
settings();

function update_settings(){
//    const dict_values = document.getElementsByClassName('settings_input'); //Pass the javascript variables to a dictionary.
    const elements = Array.from(document.getElementsByClassName("settings_input"));
    var s = [];
    for (let i = 0; i < elements.length; i++) {
	    s[i] = elements[i].value;
    }
    s = JSON.stringify(s); // Stringify converts a JavaScript object or value to a JSON string
            $.ajax({
            url:"/settings_to_map",
            type:"POST",
            contentType: "application/json",
            data: JSON.stringify(s)});
};

var adjust_settings = document.getElementById("change_settings");
adjust_settings.addEventListener("click", update_settings, false);

//pause function sets video_feed to not display and gets newest image to display instead
function pause(){
    console.log("working");
//    document.getElementById("Dummy").src = "{{ url_for('picture') }}";
};

