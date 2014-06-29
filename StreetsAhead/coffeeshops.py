import pymysql

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
        placeName, address, lat, lng = row
        lat = float(lat)
        lng = float(lng)

        # get pano location near place
        panoID, panoLat, panoLng = ingest.get_pano_function(lat, lng)

        # computing heading from pano to place
        heading = ingest.getHeading(panoLat, panoLng, lat, lng)

        print placeName, address, panoID, heading

#        panoLists = imToText.pano_to_text_function(panoID,
#                                                   panoLat,
#                                                   panoLng,
#                                                   heading,
#                                                   placeName,
#                                                   db, cur)
#        panoIDList, panoLatList, panoLngList, headingList, textList, bestPanoID, bestHeading = panoLists
