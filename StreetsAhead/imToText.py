import time
from ssl import SSLError

import unirest
from fuzzywuzzy import fuzz, process

from StreetsAhead.config import *

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
