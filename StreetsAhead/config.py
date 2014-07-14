# Store paths here, no passwords

import os
STREETSAHEAD_DIR = os.path.abspath(os.path.join(os.path.realpath(__file__), '../..'))

# Directory and files with login keys
KEY_DIR = STREETSAHEAD_DIR + "/StreetsAhead/keys"
CAMFIND_KEY_FILE = KEY_DIR + "/camfind.key" # file with CamFind API Key on first line
GOOGLE_KEY_FILE = KEY_DIR + "/google.key" # file with Google Maps API Key on first line
MYSQL_KEY_FILE = KEY_DIR + "/mysql.key" # file with mysqldb user and password on first line

# Directories for Caffe and dependencies
CAFFE_DIR = "/Users/mgeorge/insight/caffe"
LEVELDB_DIR = "/Users/mgeorge/insight/leveldbs"
PROTO_DIR = "/Users/mgeorge/insight/protos"

# Data directories
ICDAR_DIR = "/Users/mgeorge/insight/icdar2013/localization"
SVT_DIR = "/Users/mgeorge/insight/streetview_text/data"
CHARS74_DIR = "/Users/mgeorge/insight/chars74k/English"
MASTER_TRAIN_DATA_DIR = "/Users/mgeorge/insight/masterTrainData"
MASTER_VAL_DATA_DIR = "/Users/mgeorge/insight/masterValData"
