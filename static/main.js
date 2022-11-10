//var svgOverviewImage = document.getElementById("myDisplay");
//// var svgDetailImage = document.getElementById("mySnippet");
//var svgCanvas = document.getElementById('svgRoot');
//
//var overviewImage = new Image();
//var detailImage = new Image();

//let pz = createPanZoom(scene, {
//    smoothScroll: false,
//    panButton: 1,
//    filterKey: function(e) {
//        if (e.type==="keypress") canvasKeyPressed(e);
//    return true;
//  }
//});

// img_url = "{{ url_for('video_feed') }}";

// img_reload(img_url, overviewImage, svgOverviewImage, () => {});
//overviewImage.src = "video_feed";
//svgOverviewImage.href.baseVal = overviewImage.src;

//var clear = document.getElementById('#clear');
var clear = document.querySelector("#clear");
//console.log(clear)
clear.addEventListener('click',set_t0,false);

function set_t0(){
        $.ajax({
            url:"/set_t0",
            context: document.body});};

function get_ell_after_t0(){
        $.ajax({
            url:"/get_ell_after_t0"
//            type: "GET",
            });};
}
console.log(get_ell_after_t0())

function rand() {
  return Math.random();
}



Plotly.newPlot('graph', [{
  y: [1,2,3].map(rand),
  mode: 'lines',
  line: {color: '#80CAF6'}
}]);
var cnt = 0;
var interval = setInterval(function() {
  Plotly.extendTraces('graph', {
    y: [[rand()]]
  }, [0])
  if(++cnt === 100) clearInterval(interval);

}, 300);
