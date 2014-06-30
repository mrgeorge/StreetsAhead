import time
from ssl import SSLError

import unirest
from fuzzywuzzy import fuzz, process

from StreetsAhead.config import *
from StreetsAhead import ingest, cache

with open(CAMFIND_KEY_FILE, 'r') as ff:
    CAMFIND_KEY = ff.readline().replace('\n', '')

def camfindPost(imgurl, maxTries=3, sleep=1):
    nTries = 0
    while nTries < maxTries:
        try:
            post = unirest.post("https://camfind.p.mashape.com/image_requests",
                headers={"X-Mashape-Authorization": CAMFIND_KEY},
                params={
                    "image_request[locale]": "en_US",
                    "image_request[remote_image_url]": imgurl
                })
            token = post.body['token']
            return token
        except KeyError, SSLError:
            nTries += 1
            time.sleep(sleep)

    print "Warning: camfindPost failed", imgurl
    return None

def camfindGet(token, maxTries=15, sleep=1, initSleep=5):

    if token is not None:
        time.sleep(initSleep) # Camfind recommends ~5 second wait to start,
                              # then 1-2 secs between retries

        nTries = 0
        while nTries < maxTries:
            try:
                get = unirest.get("https://camfind.p.mashape.com/image_responses/" +
                              token, headers={"X-Mashape-Authorization":
                                              CAMFIND_KEY})
                return get.body['name']
            except KeyError, SSLError:
                nTries += 1
                time.sleep(sleep)

    # only get here if token is None or camfind get request failed
    print "Warning: camfindGet failed", token
    return None

def wordMatch(imgStr, queryPlaceName):
    """Return score of how well image text matches search query

    Input:
        imgStr - string of text describing image
            (e.g. "udupi palace storefront")
        queryPlaceName - string with Google Places name
            (e.g. "Udupi Palace")

    Returns:
        wordScore - best partial ratio
    """

    # WRatio uses weighted partial-string matching
    # default forces to lower case alphanumeric chars
    # high score (max 100) means good match
    return fuzz.WRatio(imgStr, queryPlaceName)

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
        tokenList.append(camfindPost(url))

    return (urlList, tokenList)

def getImageLabels(tokenList):
    """Retrieve image labels (text) from CamFind"""
    textList = [camfindGet(token) for token in tokenList]
    textList = [text if text is not None else "NULL" for text in textList]

    return textList

def pano_to_text_function(panoID, panoLat, panoLng, heading, placeName, db, cur):
    locList = ingest.getLocations(panoLat, panoLng, heading=heading)
    panoIDList = [panoID for loc in locList]
    panoLatList = [loc[0] for loc in locList]
    panoLngList = [loc[1] for loc in locList]
    headingList = [loc[2] for loc in locList]

    print panoID, headingList

    # Cache pano locations for each entry in locList
    # NOTE: currently assumes panoID is same for each loc
    # if panoID's are different, must cache each one
    cache.cache_pano(db, cur, panoID, panoLat, panoLng)

    # First check the cache to get list of missing image labels
    textList = [cache.getCacheText(db, cur, panoID, loc[2]) for loc in locList]
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
    for ii, newText, url, token in zip(missingList, newTextList, urlList, tokenList):
        if newText is not None: # got a new image text label
            textList[ii] = newText
        else:
            textList[ii] = "NULL"

        # Save new label to cache
        cache.cache_image(db, cur,
                          panoIDList[ii],
                          headingList[ii],
                          url,
                          token,
                          textList[ii])

    # Get panoID and heading for best matching text
    # if no match scores better than scoreLimit, use default pointing
    bestScore = -1
    scoreLimit = 40
    bestHeading = heading
    bestPanoID = panoID
    for thisText, thisHeading, thisPanoID in zip(textList, headingList,
                                                 panoIDList):
        score = wordMatch(thisText, placeName)
        if score > bestScore and score > scoreLimit:
            bestHeading = thisHeading
            bestPanoID = thisPanoID
        print thisText, score

    return (panoIDList,
            panoLatList,
            panoLngList,
            headingList,
            textList,
            bestPanoID,
            bestHeading)
