var svgOverviewImage = document.getElementById("myDisplay");
// var svgDetailImage = document.getElementById("mySnippet");
var svgCanvas = document.getElementById('svgRoot');

var overviewImage = new Image();
var detailImage = new Image();

let pz = createPanZoom(scene, {
    smoothScroll: false,
    panButton: 1,
    filterKey: function(e) {
        if (e.type==="keypress") canvasKeyPressed(e);
    return true;
  }
});

// img_url = "{{ url_for('video_feed') }}";

// img_reload(img_url, overviewImage, svgOverviewImage, () => {});
overviewImage.src = "video_feed";
svgOverviewImage.href.baseVal = overviewImage.src;

