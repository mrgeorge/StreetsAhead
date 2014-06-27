import pymysql

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
        name, address, lat, lng = row
        # nearestPanoID = get_pano(lat, lng)
        #  get pano loc
