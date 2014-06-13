import time

import unirest

CAMFIND_KEY_FILE = "/Users/mgeorge/insight/StreetsAhead/StreetsAhead/keys/camfind.key" # file with CamFind API Key on first line
with open(CAMFIND_KEY_FILE, 'r') as ff:
    CAMFIND_KEY = ff.readline().replace('\n', '')

def camfindPost(imgurl):
    post = unirest.post("https://camfind.p.mashape.com/image_requests",
        headers={"X-Mashape-Authorization": CAMFIND_KEY},
        params={ 
            "image_request[locale]": "en_US",
            "image_request[remote_image_url]": imgurl
        }
    )

    token = post.body['token']

    return token

def camfindGet(token, maxTries=10, sleep=1):
    nTries = 0
    while nTries < maxTries:
        get = unirest.get("https://camfind.p.mashape.com/image_responses/" + token,
                headers={"X-Mashape-Authorization": CAMFIND_KEY}
            )
        try:
            return get.body['name']
        except KeyError:
            nTries += 1
            time.sleep(sleep)

