# Store paths here, no passwords

import os
STREETSAHEAD_DIR = os.path.abspath(os.path.join(os.path.realpath(__file__), '../..'))
print STREETSAHEAD_DIR

KEY_DIR = STREETSAHEAD_DIR + "/StreetsAhead/keys"

CAMFIND_KEY_FILE = KEY_DIR + "/camfind.key" # file with CamFind API Key on first line
GOOGLE_KEY_FILE = KEY_DIR + "/google.key" # file with Google Maps API Key on first line

MYSQL_KEY_FILE = KEY_DIR + "/mysql.key" # file with mysqldb user and password on first line
