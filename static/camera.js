var video = document.querySelector("#videoElement");
var stopVideo = document.querySelector("#stop");
var startVideo = document.querySelector("#start");

if (navigator.mediaDevices.getUserMedia) {
  navigator.mediaDevices
    .getUserMedia({
      video: {
        frameRate: 25,
      },
    })
    .then(function (stream) {
      video.srcObject = stream;
    })
    .catch(function (err0r) {
      console.log("Something went wrong!");
    });

}

stopVideo.addEventListener("click", stop, false);

function stop(e) {
  var stream = video.srcObject;
  var tracks = stream.getTracks();

  for (var i = 0; i < tracks.length; i++) {
    var track = tracks[i];
    track.stop();
  }

  video.srcObject = null;
}

startVideo.addEventListener("click", start, false);

function start(){
    if (navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices
          .getUserMedia({
            video: {
              frameRate: 25,
            },
          })
          .then(function (stream) {
            video.srcObject = stream;
          })
          .catch(function (err0r) {
            console.log("Something went wrong!");
          });
      }
}

var dummy = document.querySelector("#dummy");
dummy.addEventListener("click", change_dummy, false);

function change_dummy(){
    if (document.getElementById("Dummy").style.display === "none"){
        document.getElementById("Dummy").style.display = "inline";
        document.getElementById('dummy').innerText = 'Stop Dummy-Video';}
    else {
        document.getElementById("Dummy").style.display = "none";
        document.getElementById('dummy').innerText = 'Start Dummy-Video';
    }
}