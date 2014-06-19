var SAPanoStart = "null"; // keep track of initial SA position to toggle text labels

function initialize() {
  var mapOptions = {
    center: new google.maps.LatLng(37.8717, -122.2728),
    zoom: 14
  };

  var map = new google.maps.Map(document.getElementById('map-canvas'),
    mapOptions);

  var input = /** @type {HTMLInputElement} */(
      document.getElementById('pac-input'));

  var types = document.getElementById('type-selector');
  map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);
  map.controls[google.maps.ControlPosition.TOP_LEFT].push(types);

  var autocomplete = new google.maps.places.Autocomplete(input);
  autocomplete.bindTo('bounds', map);

  var boxText = document.createElement("div");
  boxText.style.cssText = "border: 1px solid black; margin-top: 1px; background: white; padding: 10px;";
  boxText.innerHTML = "";
  var myOptions = {
                content: boxText,
                disableAutoPan: false,
                maxWidth: 0,
                pixelOffset: new google.maps.Size(-310, 30),//X axis should be half the size of box width
                zIndex: null,
                boxStyle: {
//                  background: "url('tipbox.gif') no-repeat",
                  background: "white",
                  opacity: 1.,
                  width: "610px",
                  height: "250px",
		  padding: "10px",
		  border: "1px solid black"
                 },
                closeBoxMargin: "2px 2px 2px 2px",
//                closeBoxURL: "http://www.google.com/intl/en_us/mapfiles/close.gif",
                closeBoxURL: "",
                infoBoxClearance: new google.maps.Size(10, 10),
                isHidden: false,
                pane: "floatPane",
                enableEventPropagation: false
        };

  var ib = new InfoBox(myOptions);

  var marker = new google.maps.Marker({
    map: map,
    anchorPoint: new google.maps.Point(0, -29)
  });

  google.maps.event.addListener(autocomplete, 'place_changed', function() {
    marker.setVisible(false);
    var place = autocomplete.getPlace();
    if (!place.geometry) {
      return;
    }

    // If the place has a geometry, then present it on a map.
    if (place.geometry.viewport) {
      map.fitBounds(place.geometry.viewport);
    } else {
      map.setCenter(place.geometry.location);
      map.setZoom(17);  // Why 17? Because it looks good.
    }
    marker.setIcon(/** @type {google.maps.Icon} */({
      url: place.icon,
      size: new google.maps.Size(71, 71),
      origin: new google.maps.Point(0, 0),
      anchor: new google.maps.Point(17, 34),
      scaledSize: new google.maps.Size(35, 35)
    }));
    marker.setPosition(place.geometry.location);
    marker.setVisible(true);

    var address = '';
    if (place.address_components) {
      address = [
        (place.address_components[0] && place.address_components[0].short_name || ''),
        (place.address_components[1] && place.address_components[1].short_name || ''),
        (place.address_components[2] && place.address_components[2].short_name || '')
      ].join(' ');
    }

    // Pass query info to flask view to cache in database
    $.post($SCRIPT_ROOT + '/_cache_query', {
	"placeName": place.name,
	"address": address,
	"latitude": place.geometry.location.lat(),
	"longitude": place.geometry.location.lng()
    });

    // Define contents of infobox
    var contentString = '<div id="ibtext"><strong>' + place.name + '</strong><br>'+
          address +
          '</div>'+
	  '<div id="svdoublewide">' +
            '<div class="leftbuff" style="float: left;">' +
              '<div id="SVPano" style="width: 300px; height: 200px;float:left; z-index:30;">' +
              '</div>' +
//              '<img src = "http://maps.googleapis.com/maps/api/streetview?location=37.86713,-122.258677&heading=0&fov=50&size=300x200"/>' +
              '<p id="imtext" style="text-align: center">Street View</p>' +
            '</div>' +
            '<div class="rightbuff" style="float: right;">' +
              '<div id="SAPano" style="width: 300px; height: 200px;float:left; z-index:30;">' +
              '</div>' +
//              '<img src = "http://maps.googleapis.com/maps/api/streetview?location=37.86713,-122.258677&heading=0&fov=50&size=300x200"/>' +
              '<p id="imtext" style="text-align: center">StreetsAhead</p>' +
            '</div>' +
          '</div>';

    ib.setContent(contentString);
    ib.open(map, marker);


    // Once the infobox html is loaded to DOM, we can modify and render the pano div
    google.maps.event.addListener(ib, "domready", function() {
      var SVPanoOptions = {
        position: place.geometry.location,
        pov: {
          heading: 0,
          pitch: 0
        },
        zoom: 1,
	panControl: false,
	zoomControl: false,
	addressControl: false,
	linksControl: false
      };
      var SVPano = new google.maps.StreetViewPanorama(
        document.getElementById('SVPano'),
        SVPanoOptions);
      var SAPano = new google.maps.StreetViewPanorama(
        document.getElementById('SAPano'),
        SVPanoOptions);
      var SAMarkerList = []

      // Get nearest panorama location and heading relative to place

      // This approach uses jQuery call with flask to _get_pano which uses
      // an unofficial API (xml file) to get Google's guess for the
      // best pano id. Using getPanoramaByLocation often gives indoor images
      // which are not desired.
      var panoGuess = 'def';
      $.getJSON($SCRIPT_ROOT + '/_get_pano', {
	"latitude": place.geometry.location.lat(),
	"longitude": place.geometry.location.lng()
        }, function(data) {
	  panoGuess = data.pano_id;
          SAPanoStart = panoGuess;

          var SVService = new google.maps.StreetViewService();
//      SVService.getPanoramaByLocation(place.geometry.location, 50, function (panoData, status) {
          SVService.getPanoramaById(panoGuess, function (panoData, status) {
            if(status === google.maps.StreetViewStatus.OK){
              var panoLoc = panoData.location.latLng;
              var heading = google.maps.geometry.spherical.computeHeading(panoLoc, place.geometry.location);
//          SVPano.setPosition(panoLoc);
              SVPano.setPano(panoGuess);
              SVPano.setPov({
                heading: heading,
                pitch: 0
              });

// for debugging
//          var headingCell = document.getElementById('heading_cell');
//          headingCell.firstChild.nodeValue = SVPano.getPov().heading + ''; 
//          var panoCell = document.getElementById('pano_cell');
//          panoCell.innerHTML = SVPano.getPano();
//          panoCell.innerHTML = panoGuess;


// pass pano id, lat, lng, heading to flask.
// get back arrays with pano ids (may include neighbor links), pano lats, pano lngs, headings, texts (all arrays equal length 3 to start)
// make SAPano
// iterate over list and make marker for each
              $.getJSON($SCRIPT_ROOT + '/_pano_to_text', {
                "panoId": panoGuess,
                "panoLat": panoLoc.lat(),
                "panoLng": panoLoc.lng(),
                "heading": heading
                }, function(results) {
                  var len = results.textList.length;
                  for (var ii = 0; ii < len; ii++) {
		    var thisPanoPos = new google.maps.LatLng(results.panoLatList[ii], results.panoLngList[ii]);
                    var thisMarkerPos = google.maps.geometry.spherical.computeOffset(thisPanoPos, 10., results.headingList[ii]);
		    var thisMarker = new MarkerWithLabel({
                      position: thisMarkerPos,
                      clickable: false,
                      opacity: 0.,
                      labelVisible: true,
                      draggable: false,
                      raiseOnDrag: false,
                      map: SAPano,
                      labelContent: results.textList[ii],
                      labelAnchor: new google.maps.Point(22, 0),
                      labelClass: "svlabels", // the CSS class for the label
                      labelStyle: {opacity: 0.5}
                    });

                    SAMarkerList.push(thisMarker);
                  }
              });

            }else{
              $this.text("Sorry! Street View is not available.");
              // no street view available in this range, or some error occurred
            }
          });
      });

/*      var len = SAMarkerList.length;
      for (var jj = 0; jj < len; jj++) {
        SAMarkerList[jj].setMap(SAPano);
      }
*/
      SVPano.setVisible(true);
      SAPano.setVisible(true);



      // Text label doesn't render well after moving from initial point
      // hide it when current pano ID differs from original
      google.maps.event.addListener(SAPano, 'pano_changed', function() {
        if (SAPano.getPano() == SAPanoStart) {
//          marker1.setVisible(true);
//          marker1.set("labelContent", SAPanoStart + SAPano.getPano());
        } else {
//          marker1.setVisible(false);
//          marker1.set("labelContent", "moved" + SAPanoStart + SAPano.getPano());
        }
      });
    });
  });
}

google.maps.event.addDomListener(window, 'load', initialize);
