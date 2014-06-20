from flask import render_template, flash, redirect, jsonify, request
from app import app, host, port, user, passwd, db
from app.helpers.database import con_db
from forms import EntryForm

import urllib2
from BeautifulSoup import BeautifulStoneSoup

import pymysql

db = pymysql.connect(user="flask", host="localhost", port=3306, db="StreetsAhead")
cur = db.cursor()

try:
    from StreetsAhead import ingest, imToText
except ImportError: # add parent dir to python search path
    import os, sys
    path, filename = os.path.split(__file__)
    sys.path.append(os.path.abspath(os.path.join(path,"../../../StreetsAhead")))
    from StreetsAhead import ingest, imToText


class Image(object):
    def __init__(self, url, token, text):
        self.url = url
        self.token = token
        self.text = text

def queryToLocs(form):
    inputQuery = form.query.data
    keywordStr, locStr = inputQuery.split(',')
    place = ingest.getPlaceFromQuery(keywordStr, locStr)

    locs = ingest.getLocations(place.geo_location['lat'],
                                   place.geo_location['lng'])
    return locs

def locsToImages(locs):
    images = []
    for loc in locs:
        lat, lng, heading = loc
        url = ingest.getImageUrl(lat, lng, heading)
        token = imToText.camfindPost(url)
        if token is not None:
            images.append(Image(url, token, None))

    descriptions = ""
    for image in images:
        text = imToText.camfindGet(image.token)
        if text is not None:
            image.text = text
        else:
            image.text = "NULL"

    return images

# ROUTING/VIEW FUNCTIONS
@app.route('/')
def landing():
    return render_template('landing.html')

#@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
@app.route('/search', methods = ['GET', 'POST'])
@app.route('/results', methods = ['GET', 'POST'])
def index():
    # Renders index.html.
    form = EntryForm()
    if form.validate_on_submit():
        images = locsToImages(queryToLocs(form))
        return render_template('results.html', images=images, form=form)
    return render_template('search.html', form=form)

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

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/_cache_query', methods = ['POST'])
def cache_query():
    """Called by ajax post in places.js to get place info to python

    Cache location to places table in SQL db.
    """
    placeName = request.form['placeName']
    address = request.form['address']
    lat = float(request.form['latitude'])
    lng = float(request.form['longitude'])
    cur.execute("""INSERT INTO places
        (placename, address, latitude, longitude)
        VALUES (%s, %s, %s, %s);""",
        (placeName, address, lat, lng))
    db.commit()

    print "executed cache query"
    return jsonify(result=0)

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

    panoId = request.args.get('panoId', 'NULL')
    panoLat = float(request.args.get('panoLat', 0.))
    panoLng = float(request.args.get('panoLng', 0.))
    heading = float(request.args.get('heading', 0.))
    placeName = request.args.get('placeName', 'NULL')

    print panoId, placeName

    locs = ingest.getLocations(panoLat, panoLng, heading=heading)
#    images = locsToImages(locs)
#    locs = []
#    images = []

    panoIdList = [panoId for loc in locs]
    panoLatList = [loc[0] for loc in locs]
    panoLngList = [loc[1] for loc in locs]
    headingList = [loc[2] for loc in locs]
#    textList = [img.text for img in images]

    print panoId, headingList

    textList = [getCacheText(panoId, loc[2]) for loc in locs]
    for ii, text in enumerate(textList):
        if text is None:
            img = locsToImages([locs[ii]])
            if len(img) > 0:
                textList[ii] = img[0].text
            else:
                textList[ii] = "NULL"

    # Get panoId and heading for best matching text
    # if no match scores better than scoreLimit, use default pointing
    bestScore = -1
    scoreLimit = 40
    bestHeading = heading
    bestPanoId = panoId
    for thisText, thisHeading, thisPanoId in zip(textList, headingList,
                                                 panoIdList):
        score = imToText.wordMatch(thisText, placeName)
        if score > bestScore and score > scoreLimit:
            bestHeading = thisHeading
            bestPanoId = thisPanoId
        print score


    return jsonify({"panoIdList": panoIdList,
                    "panoLatList": panoLatList,
                    "panoLngList": panoLngList,
                    "headingList": headingList,
                    "textList": textList,
                    "bestPanoId": bestPanoId,
                    "bestHeading": bestHeading})

def getCacheText(panoId, heading):
    cur.execute("""SELECT text FROM imtext
                   WHERE panoId = %s
                   AND heading BETWEEN %s AND %s""",
                   (panoId, heading-10, heading+10))
    try:
        text = cur.fetchone()[0]
        return text
    except TypeError:
        return None
