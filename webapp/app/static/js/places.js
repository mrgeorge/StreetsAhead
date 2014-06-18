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
              '<p id="imtext">Street View</p>' +
            '</div>' +
            '<div class="rightbuff" style="float: right;">' +
              '<div id="SAPano" style="width: 300px; height: 200px;float:left; z-index:30;">' +
              '</div>' +
//              '<img src = "http://maps.googleapis.com/maps/api/streetview?location=37.86713,-122.258677&heading=0&fov=50&size=300x200"/>' +
              '<p id="imtext">StreetsAhead</p>' +
            '</div>' +
          '</div>';

    ib.setContent(contentString);
    ib.open(map, marker);

    google.maps.event.addListener(ib, "domready", function() {
      var SVPanoOptions = {
        position: place.geometry.location,
        pov: {
          heading: 165,
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

      var SAPanoOptions = {
        position: place.geometry.location,
        pov: {
          heading: 165,
          pitch: 0
        },
        zoom: 1,
	panControl: false,
	zoomControl: false,
	addressControl: false,
	linksControl: false
      };
      var SAPano = new google.maps.StreetViewPanorama(
        document.getElementById('SAPano'),
        SAPanoOptions);

      SVPano.setVisible(true);
      SVPano.setVisible(true);
    });
  });
}

google.maps.event.addDomListener(window, 'load', initialize);
