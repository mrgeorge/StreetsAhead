from flask import render_template, flash, redirect, jsonify, request
from app import app, host, port, user, passwd, db
from app.helpers.database import con_db

import pymysql

try:
    from StreetsAhead import ingest, imToText
    from StreetsAhead.config import *
except ImportError: # add parent dir to python search path
    import os, sys
    path, filename = os.path.split(__file__)
    sys.path.append(os.path.abspath(os.path.join(path,"../../../StreetsAhead")))
    from StreetsAhead import ingest, imToText, cache
    from StreetsAhead.config import *

with open(MYSQL_KEY_FILE, 'r') as ff:
    username, password = ff.readline().split()
db = pymysql.connect(user=username, passwd=password, host="localhost",
                     port=3306, db="StreetsAhead")
cur = db.cursor()

# ROUTING/VIEW FUNCTIONS
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/slides')
def about():
    # Renders slides.html.
    return render_template('slides.html')

@app.route('/faq')
def contact():
    # Renders author.html.
    return render_template('faq.html')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.route('/go')
def go():
    return render_template('go.html')

# ASYNCHRONOUS HANDLERS
@app.route('/_cache_place', methods = ['POST'])
def cache_place_handler():
    """Called by ajax post in places.js to get place info to python"""
    placeName = request.form['placeName']
    address = request.form['address']
    lat = float(request.form['latitude'])
    lng = float(request.form['longitude'])
    panoID = request.form['panoID']

    result = cache.cache_place_function(db,
                                        cur,
                                        placeName,
                                        address,
                                        lat,
                                        lng,
                                        panoID)

    print "executed cache_place"
    return jsonify(result=result)

@app.route('/_get_pano')
def get_pano_handler():
    """Called by ajax post in places.js to get best outdoor pano from xml api"""
    lat = float(request.args.get('latitude', 0.))
    lng = float(request.args.get('longitude', 0.))

    pano_id, pano_lat, pano_lng = ingest.get_pano_function(lat, lng)

    return jsonify(pano_id=pano_id)

@app.route('/_pano_to_text')
def pano_to_text_handler():
    """Given panoID and location, get text labels for nearby images"""
    panoID = request.args.get('panoId', 'NULL')
    panoLat = float(request.args.get('panoLat', 0.))
    panoLng = float(request.args.get('panoLng', 0.))
    heading = float(request.args.get('heading', 0.))
    placeName = request.args.get('placeName', 'NULL')

    print panoID, panoLat, panoLng, heading, placeName

    panoLists = imToText.pano_to_text_function(panoID,
                                               panoLat,
                                               panoLng,
                                               heading,
                                               placeName,
                                               db, cur)
    panoIDList, panoLatList, panoLngList, headingList, textList, bestPanoID, bestHeading = panoLists

    return jsonify({"panoIdList": panoIDList,
                    "panoLatList": panoLatList,
                    "panoLngList": panoLngList,
                    "headingList": headingList,
                    "textList": textList,
                    "bestPanoId": bestPanoID,
                    "bestHeading": bestHeading})
