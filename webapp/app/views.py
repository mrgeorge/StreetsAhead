from flask import render_template, flash, redirect, jsonify, request
from app import app, host, port, user, passwd, db
from app.helpers.database import con_db
from forms import EntryForm

import urllib2
from BeautifulSoup import BeautifulStoneSoup

import pymysql
from pymysql import IntegrityError

try:
    from StreetsAhead import ingest, imToText
    from StreetsAhead.config import *
except ImportError: # add parent dir to python search path
    import os, sys
    path, filename = os.path.split(__file__)
    sys.path.append(os.path.abspath(os.path.join(path,"../../../StreetsAhead")))
    from StreetsAhead import ingest, imToText
    from StreetsAhead.config import *

with open(MYSQL_KEY_FILE, 'r') as ff:
    username, password = ff.readline().split()
db = pymysql.connect(user=username, passwd=password, host="localhost",
                     port=3306, db="StreetsAhead")
cur = db.cursor()

class Image(object):
    def __init__(self, url, token, text):
        self.url = url
        self.token = token
        self.text = text

def queryToLocList(form):
    inputQuery = form.query.data
    keywordStr, locStr = inputQuery.split(',')
    place = ingest.getPlaceFromQuery(keywordStr, locStr)

    locList = ingest.getLocations(place.geo_location['lat'],
                                   place.geo_location['lng'])
    return locList

def postImages(locList):
    """Given locations, submit images to CamFind

    Returns url list and token list (without text attr filled in)

    Note: want to leave as much time as reasonable between calls to
        camfindPost (postImages) and camfindGet (getImageLabels)
    """

    urlList = []
    tokenList = []
    for loc in locList:
        lat, lng, heading = loc
        url = ingest.getImageUrl(lat, lng, heading)
        urlList.append(url)
        tokenList.append(imToText.camfindPost(url))

    return (urlList, tokenList)

def getImageLabels(tokenList):
    """Retrieve image labels (text) from CamFind"""
    textList = [imToText.camfindGet(token) for token in tokenList]
    textList = [text if text is not None else "NULL" for text in textList]

    return textList

# ROUTING/VIEW FUNCTIONS
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/slides')
def about():
    # Renders slides.html.
    return render_template('slides.html')

@app.route('/author')
def contact():
    # Renders author.html.
    return render_template('author.html')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.route('/go')
def go():
    return render_template('go.html')

# ASYNCHRONOUS FUNCTIONS AND SUPPORT
@app.route('/_cache_place', methods = ['POST'])
def cache_place():
    """Called by ajax post in places.js to get place info to python

    Cache location to places table in SQL db.
    """
    placeName = request.form['placeName']
    address = request.form['address']
    lat = float(request.form['latitude'])
    lng = float(request.form['longitude'])
    panoID = request.form['panoID']

    db.ping(True)
    cur.execute("""INSERT INTO places
                   (placename, address, latitude, longitude, panoID)
                   VALUES (%s, %s, %s, %s, %s);""",
                   (placeName, address, lat, lng, panoID))
    db.commit()

    print "executed cache_place"
    return jsonify(result=0)

def cache_pano(panoID, panoLat, panoLng):
    db.ping(True)
    try:
        cur.execute("""INSERT INTO panoLocs (panoID, panoLat, panoLng)
                       VALUES (%s, %s, %s)""", (panoID, panoLat, panoLng))
        db.commit()
    except IntegrityError:
        # Ignore if panoID is already stored in table
        pass

    print "executed cache_pano"
    return jsonify(result=0)

def cache_image(panoID, heading, url, token, text):
    """Insert panorama details into database

    Note: some info may not be available, e.g. if CamFind times out
    """
    db.ping(True)
    cur.execute("""INSERT INTO images
                   (panoID, heading, url, camfindToken, text)
                   VALUES (%s, %s, %s, %s, %s);""",
                   (panoID, heading, url, token, text))
    db.commit()
    print "executed cache image"

@app.route('/_get_pano')
def get_pano():
    """Called by ajax post in places.js to get best outdoor pano from xml api

    See discussion here: http://stackoverflow.com/questions/14796604/how-to-know-if-street-view-panorama-is-indoors-or-outdoors

    This is a hacky way to get Google's guess for the best outdoor pano for
    a given location.
    """
    lat = float(request.args.get('latitude', 0.))
    lng = float(request.args.get('longitude', 0.))

    urlbase = "http://cbk0.google.com/cbk?output=xml&hl=x-local"
    ff = urllib2.urlopen("{}&ll={},{}".format(urlbase, lat, lng))
    xml = ff.read()
    ff.close()

    bs = BeautifulStoneSoup(xml)
    allDP = bs.findAll("data_properties")
    if len(allDP) > 0:
        dp = allDP[0]
        pano_id = [attr[1] for attr in dp.attrs if attr[0]=='pano_id'][0]
    else:
        pano_id = "NULL"

    return jsonify(pano_id=pano_id)

@app.route('/_pano_to_text')
def pano_to_text():

    panoID = request.args.get('panoId', 'NULL')
    panoLat = float(request.args.get('panoLat', 0.))
    panoLng = float(request.args.get('panoLng', 0.))
    heading = float(request.args.get('heading', 0.))
    placeName = request.args.get('placeName', 'NULL')

    print panoID, placeName

    locList = ingest.getLocations(panoLat, panoLng, heading=heading)
    panoIDList = [panoID for loc in locList]
    panoLatList = [loc[0] for loc in locList]
    panoLngList = [loc[1] for loc in locList]
    headingList = [loc[2] for loc in locList]

    print panoID, headingList

    # Cache pano locations for each entry in locList
    # NOTE: currently assumes panoID is same for each loc
    # if panoID's are different, must cache each one
    cache_pano(panoID, panoLat, panoLng)

    # First check the cache to get list of missing image labels
    textList = [getCacheText(panoID, loc[2]) for loc in locList]
    missingList = []
    for ii, text in enumerate(textList):
        if text is None or text == "NULL":
            missingList.append(ii)
    missingLocList = [locList[ii] for ii in missingList]

    # Run CamFind on images that aren't cached
    urlList, tokenList = postImages(missingLocList)

    # Get CamFind results (may take a while)
    newTextList = getImageLabels(tokenList)

    # Update textList with any new labels we received
    for ii, newText in zip(missingList, newTextList):
        if newText is not None: # got a new image text label
            textList[ii] = newText
        else:
            textList[ii] = "NULL"

        # Save new label to cache
        cache_image(panoIDList[ii],
                    headingList[ii],
                    urlList[ii],
                    tokenList[ii],
                    textList[ii])

    # Get panoID and heading for best matching text
    # if no match scores better than scoreLimit, use default pointing
    bestScore = -1
    scoreLimit = 40
    bestHeading = heading
    bestPanoID = panoID
    for thisText, thisHeading, thisPanoID in zip(textList, headingList,
                                                 panoIDList):
        score = imToText.wordMatch(thisText, placeName)
        if score > bestScore and score > scoreLimit:
            bestHeading = thisHeading
            bestPanoID = thisPanoID
        print thisText, score

    return jsonify({"panoIdList": panoIDList,
                    "panoLatList": panoLatList,
                    "panoLngList": panoLngList,
                    "headingList": headingList,
                    "textList": textList,
                    "bestPanoId": bestPanoID,
                    "bestHeading": bestHeading})

def getCacheText(panoID, heading, deltaHeading=10.):
    """Check if image text already exists and if so return it, else None"""
    db.ping(True)
    cur.execute("""SELECT text FROM images
                   WHERE panoId = %s
                   AND heading BETWEEN %s AND %s""",
                   (panoID, heading-deltaHeading, heading+deltaHeading))
    try:
        text = cur.fetchone()[0]
        return text
    except TypeError:
        return None
