import re
import urllib
import numpy as np

import googleplaces
import cv2

API_KEY_FILE = "keys/google.key" # file with Google Maps API Key on first line
with open(API_KEY_FILE, 'r') as ff:
    API_KEY = ff.readline().replace('\n', '')
gp = googleplaces.GooglePlaces(API_KEY)

inputKeywordStr = "Zachary's"
#inputKeywordStr = "CREAM"
inputLocationStr = "Berkeley, CA"

def getPlaceFromQuery(inputKeywordStr, inputLocationStr):
    """Convert search query text into place object"""
    places = gp.nearby_search(keyword=inputKeywordStr,
                              location=inputLocationStr)
    place = places.places[0] # take top listed place (sorted by prominence)
    return place
    
def getQueryListFromPlace(place):
    """Return list of words to find in image

    queryList includes address number and words in business name
    """
    queryList = []

    # searchStr for number at start of address
    addressNumberStr = re.search("^\d*", place.vicinity).group(0)
    if addressNumberStr:
        queryList.append(addressNumberStr)

    # splits words on space, remove bad chars
    # retain list of words and address number for later comparison
    nameWords = [re.sub('\W+','', name) for name in place.name.split(' ')]
    queryList.extend(nameWords)

    return queryList

def getLocations(lat0, lng0):
    """Generate list of (lat, lng) coordinates near initial search position"""
    # TODO - expand search list to neighboring points along road
    lats = [lat0, lat0, lat0]
    lngs = [lng0, lng0, lng0]
    headings = [0, 45, 315]
    return zip(lats, lngs, headings)

def getImage(lat, lng, heading, size="640x640", fov=50):
    """Call StreetView API to get image for coordinates"""

    urlbase = "http://maps.googleapis.com/maps/api/streetview"

    url = "{urlbase}?location={lat},{lng}&heading={heading}&fov={fov}&size={size}".format(urlbase=urlbase, lat=lat, lng=lng, heading=heading, fov=fov, size=size)

    #http://stackoverflow.com/questions/21061814/how-can-i-read-an-image-from-an-internet-url-in-python-cv2-scikit-image-and-ma
    req = urllib.urlopen(url)
    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
    img = cv2.imdecode(arr, -1)

    return img    

if __name__ == "__main__":

    place = getPlaceFromQuery(inputKeywordStr, inputLocationStr)
    queryList = getQueryListFromPlace(place)

    locs = getLocations(place.geo_location['lat'], place.geo_location['lng'])
    imgList = []
    for loc in locs:
        lat, lng, heading = loc
        imgList.append(getImage(lat, lng, heading))

