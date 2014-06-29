import pymysql
import time

import ingest, imToText

db = pymysql.connect(user="guest", host="localhost", port=3306, db="yelp")
cur = db.cursor()

categories = ("starbuck", "peet's", "philz", "blue bottle") # stem names
nMax = 50 # pick at most nMax of any category

query = """SELECT name, display_address, latitude, longitude
           FROM yelp
           WHERE name LIKE %s
           ORDER BY RAND()
           LIMIT %s"""

for category in categories:
    args = ('%'+category+'%', nMax)
    cur.execute(query, args)

    for row in cur.fetchall():
        time.sleep(0.2)
        placeName, address, mqlat, mqlng = row

        # use google's coordinates instead of mapquest's
        try:
            location = ingest.locateAddress(placeName + " " + address)[0]
        except IndexError:
            try:
                location = ingest.locateAddress(address)[0]
            except IndexError:
                print "Warning: unable to locate", placeName, address
                continue
        lat = location.geo_location["lat"]
        lng = location.geo_location["lng"]

        # get pano location near place
        panoID, panoLat, panoLng = ingest.get_pano_function(lat, lng)

        print lat, lng, panoLat, panoLng

        if panoID == "NULL":
            print "Warning: no pano found for ", placeName, address
            continue

        # computing heading from pano to place
        heading = ingest.getHeading(lat, lng, panoLat, panoLng)

        print placeName, address, panoID, panoLat, panoLng, heading

#        panoLists = imToText.pano_to_text_function(panoID,
#                                                   panoLat,
#                                                   panoLng,
#                                                   heading,
#                                                   placeName,
#                                                   db, cur)
#        panoIDList, panoLatList, panoLngList, headingList, textList, bestPanoID, bestHeading = panoLists
