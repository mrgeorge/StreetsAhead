from pymysql import IntegrityError

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
                       VALUES (%s, %s, %s)""", (panoID, panoLat, panoLng))
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

def getCacheText(db, cur, panoID, heading, deltaHeading=10.):
    """Check if image text already exists and if so return it, else None"""
    db.ping(True)
    cur.execute("""SELECT text FROM images
                   WHERE panoId = %s
                   AND heading BETWEEN %s AND %s""",
                   (panoID,
                    float(heading-deltaHeading),
                    float(heading+deltaHeading)))
    try:
        text = cur.fetchone()[0]
        return text
    except TypeError:
        return None
