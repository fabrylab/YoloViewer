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
//    document.getElementById("Dummy").src ="/video_feed";
   if (document.getElementById("Dummy").style.display === "none"){
        document.getElementById("Dummy").style.display = "inline";
        get_limited();
        $('#dummy').find("i").toggleClass("fa-play fa-stop");
        $('#pause').find("i").toggleClass("fa-play fa-pause");
        }
   else if (document.getElementById("Dummy").style.display === "inline"){
        document.getElementById("Dummy").style.display = "none";
        stop_interval();
        $('#dummy').find("i").toggleClass("fa-stop fa-play");
        $('#pause').find("i").toggleClass("fa-pause fa-play");
        }
   else {
       console.log("ERROR");
    }
};


var camera_output;
function gain(){
        fetch('http://127.0.0.1:5000/camera')
        .then(response => response.json())
        .then(result => {
        camera_output = JSON.parse(result);
        })
        .then(() => {
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
        .then(() => {
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
        .then(() => {
                        var streamAcquisitionDummy2 = json2array(tasks.streamAcquisitionDummy2); //second from left
                        var mechanical = json2array(tasks.mechanical); //second from right
                        var detect = json2array(tasks.detect); //first from right
                        var pylonFlask = json2array(tasks.pylonFlask); //first from left
                        if (streamAcquisitionDummy2 == "true"){
                            document.getElementById("aqc_light").style.color = "DodgerBlue";
                            }
                        else if (streamAcquisitionDummy2 == "false"){
                            document.getElementById("aqc_light").style.color = "grey";
                        }
                        if (mechanical == "true"){
                            document.getElementById("mechanical_light").style.color = "DodgerBlue";
                            }
                        else if (mechanical == "false"){
                            document.getElementById("mechanical_light").style.color = "grey";
                        }
                        if (detect == "true"){
                            document.getElementById("detect_light").style.color = "DodgerBlue";
                            }
                        else if (detect == "false"){
                            document.getElementById("detect_light").style.color = "grey";
                        }
                        if (pylonFlask == "true"){
                            document.getElementById("flask_light").style.color = "DodgerBlue";
                            }
                        else if (pylonFlask == "false"){
                            document.getElementById("flask_light").style.color = "grey";
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
                        Plotly.newPlot('graph',data, layout)
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
                        Plotly.newPlot('graph2',data, layout)
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

//pause function sets video_feed to not display and gets newest image to display instead
var vid = document.getElementById("Dummy");
var pause_button = document.getElementById("pause");
var swap_pause_status = "on";
//pause_button.addEventListener("click", pauseVid, false);
pause_button.addEventListener("click", swap_pause, false);
if (vid.style.display="none"){
    $('#pause').find("i").toggleClass("fa-pause fa-play");
};

function swap_pause() {
    if (swap_pause_status === "on"){
        swap_pause_status = "off";
        stop_interval();
        single_picture();
//        document.getElementById("dummy").removeEventListener('click', change_dummy);
        $('#pause').find("i").toggleClass("fa-pause ");
    }
    else if (swap_pause_status === "off"){
        swap_pause_status = "on";
        get_limited();
        $('#pause').find("i").toggleClass("fa-play fa-pause");
//        dummy.addEventListener("click", change_dummy, false);
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
//                console.log(obj);
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

var add_overlay = document.getElementById("overlay");
add_overlay.addEventListener("click", get_overlay, false);

let intervalId2;
function get_overlay(){
//            $.ajax({
//            url:"/overlay",
//            context: document.body});

//            fetch('http://127.0.0.1:5000/background1')
//            .then(response => response.json())
//            .then(result => {
//            obj = JSON.parse(result);
//            })
//            .then(() => {
//                console.log(obj);
//                document.getElementById("overlay_picture_div").style.display="inline";
//           });
//           $("#test").attr("src", "/background1");
    intervalId2 = setInterval(function(){
        $("#overlay1").attr("src", "/background1?time="+new Date().getTime());
        $("#overlay2").attr("src", "/background2?time="+new Date().getTime());
        $("#overlay3").attr("src", "/background3?time="+new Date().getTime());
    }, 3000);
};

function single_picture(){
        $("#Dummy").attr("src", "/picture");
};

let intervalId;

function get_limited(){
//    intervalId = setInterval(single_picture, 1000/60);
    update_picture();
};

function stop_interval(){
    clearInterval(intervalId);
};


function update_picture(){
    intervalId = setInterval(function(){
        $("#Dummy").attr("src", "/picture?time="+new Date().getTime());
    }, 1000/10);
}
