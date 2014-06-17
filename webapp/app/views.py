from flask import render_template, flash, redirect, jsonify, request
from app import app, host, port, user, passwd, db
from app.helpers.database import con_db
from forms import EntryForm

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

def queryToImages(form):
    inputQuery = form.query.data
    keywordStr, locStr = inputQuery.split(',')
    place = ingest.getPlaceFromQuery(keywordStr, locStr)
    queryList = ingest.getQueryListFromPlace(place)

    locs = ingest.getLocations(place.geo_location['lat'],
                                   place.geo_location['lng'])
    images = []
    for loc in locs:
        lat, lng, heading = loc
        url = ingest.getImageUrl(lat, lng, heading)
        token = imToText.camfindPost(url)
        images.append(Image(url, token, None))

    descriptions = ""
    for image in images:
        text = imToText.camfindGet(image.token)
        if text is not None:
            image.text = text
        else:
            image.text = "NO TEXT FOUND"

    cur.execute('INSERT INTO query (text) VALUES (%s);', (inputQuery,))
    db.commit()

    return images

# ROUTING/VIEW FUNCTIONS
@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
@app.route('/search', methods = ['GET', 'POST'])
@app.route('/results', methods = ['GET', 'POST'])
def index():
    # Renders index.html.
    form = EntryForm()
    if form.validate_on_submit():
        images = queryToImages(form)
        return render_template('results.html', images=images, form=form)
    return render_template('search.html', title='Search string', form=form)

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
