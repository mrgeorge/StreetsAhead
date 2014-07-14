StreetsAhead
============

StreetsAhead is the code repository for
[StreetsAheadMaps.com](StreetsAheadMaps.com). The website is an image
recognition tool to enhance search results from Google Street View. When you
look up a location, it searches nearby Street View images for the name and
address and points you to the right place.


How it works
============

StreetsAhead currently uses the [CamFind](http://camfindapp.com) API which
employs computer vision techniques and human labelers. A second option uses a
deep convolutional neural network built with
[Caffe](http://caffe.berkeleyvision.org) and trained on the [Street View
Text](http://vision.ucsd.edu/~kai/svt/),
[ICDAR2013](http://dag.cvc.uab.es/icdar2013competition/), and
[Chars74K](http://www.ee.surrey.ac.uk/CVSSP/demos/chars74k/) data sets.
Currently CamFind offers greater accuracy at the expense of slower evaluation
time. Original queries take roughly 20 seconds for image labels, and results are
cached in a MySQL database for faster followup responses.

Code for the web app is based on
[InsightFL](https://github.com/stormpython/insightfl)
and uses Flask and jQuery. The Google Places and Street View APIs are used for
geolocation and images.
