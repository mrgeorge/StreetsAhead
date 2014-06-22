import os
STREETSAHEAD_DIR = os.path.abspath(os.path.join(os.path.realpath(__file__), '../..'))
print STREETSAHEAD_DIR

CAMFIND_KEY_FILE = STREETSAHEAD_DIR + "/StreetsAhead/keys/camfind.key" # file with CamFind API Key on first line
GOOGLE_KEY_FILE = STREETSAHEAD_DIR + "/StreetsAhead/keys/google.key" # file with Google Maps API Key on first line
