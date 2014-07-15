from pymysql import IntegrityError
import pandas as pd

import StreetsAhead

def cache_place_function(db, cur, placeName, address, lat, lng, panoID):
    """Cache location to places table in SQL db."""

    db.ping(True)
    cur.execute("""INSERT INTO places
                   (placename, address, latitude, longitude, panoID)
                   VALUES (%s, %s, %s, %s, %s);""",
                   (placeName, address, lat, lng, panoID))
    db.commit()
    return 0

def cache_pano(db, cur, panoID, panoLat, panoLng):
    db.ping(True)
    try:
        cur.execute("""INSERT INTO panoLocs (panoID, panoLat, panoLng)
                       VALUES (%s, %s, %s);""", (panoID, panoLat, panoLng))
        db.commit()
    except IntegrityError:
        # Ignore if panoID is already stored in table
        pass

    print "executed cache_pano"

def cache_image(db, cur, panoID, heading, url, token, text):
    """Insert panorama details into database

    Note: some info may not be available, e.g. if CamFind times out
    """
    db.ping(True)
    cur.execute("""INSERT INTO images
                   (panoID, heading, url, camfindToken, text)
                   VALUES (%s, %s, %s, %s, %s);""",
                   (panoID, float(heading), url, token, text))
    db.commit()
    print "executed cache_image"

def getCacheText(db, cur, panoID, heading, deltaHeading=5.):
    """Check if image text already exists and if so return it, else None"""
    db.ping(True)
    cur.execute("""SELECT text FROM images
                   WHERE panoId = %s
                   AND heading BETWEEN %s AND %s;""",
                   (panoID,
                    float(heading-deltaHeading),
                    float(heading+deltaHeading)))
    try:
        text = cur.fetchone()[0]
        return text
    except TypeError:
        return None

def updateMissedGets(db, cur):
    """Try again to get missing image labels for entries with post tokens"""
    db.ping(True)
    cur.execute("""SELECT imageID, camfindToken
                   FROM images
                   WHERE text = "NULL"
                   AND camfindToken != "NULL";
                """)
    tokenList = []
    imageIDList = []
    for row in cur.fetchall():
        imageID, camfindToken = row
        imageIDList.append(imageID)
        tokenList.append(camfindToken)
    textList = StreetsAhead.imToText.getImageLabels(tokenList)

    updateCount = 0
    for imageID, text in zip(imageIDList, textList):
        if text != "NULL":
            cur.execute("""UPDATE images
                           SET text = %s
                           WHERE imageID = %s;
                        """, (text, imageID))
            updateCount += 1
    print "updateMissedGets retreived {} missing labels".format(updateCount)

def appendCSVToTable(db, cur, tableName, csvFile, index_col=None):
    """Copy CSV data to database table.

    Built to append results for coffeeshop test with Yelp locations into
    main database.

    Inputs:
        db, cur - sql db and cursor objects
        tableName - string name of table in SQL database
        csvFile - string name with path of CSV file from SQL dump
        index_col - column number to use as index (default = None)
                    Passed as arg to pd when reading data frame.
                    Index is assumed to be auto incremented in SQL table
                       so CSV index value is not inserted.
    """

    df = pd.read_csv(csvFile, index_col=index_col)
    df.fillna("NULL", inplace=True)
    colNames = "({})".format(','.join(df.columns))
    placeHolders = "({})".format(','.join(['%s']*len(df.columns)))
    query = "INSERT IGNORE INTO {} {} VALUES {}".format(tableName,
                                                 colNames,
                                                 placeHolders)
    data = [tuple(row[1].values) for row in df.iterrows()]
    cur.executemany(query, data)
    db.commit()

    print "Appended {} to {}.{}".format(csvFile, db.db, tableName)
