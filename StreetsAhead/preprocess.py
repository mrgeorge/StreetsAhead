import os
import glob
import string
import re

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from BeautifulSoup import BeautifulStoneSoup

CAFFE_DIR = "/Users/mgeorge/insight/caffe"
LEVELDB_DIR = "/Users/mgeorge/insight/leveldbs"
PROTO_DIR = "/Users/mgeorge/insight/protos"
MAX_L = 5 # longest string to look for
N_NETS = MAX_L + 1 # one network for each char + one for length fig 12 1312.6082

def getLabelEncoder():
    """Define A-Z, a-z, 0-9, '' as classes and encode to integers"""
    classes = list(string.letters + string.digits)
    classes.append('')
    le = LabelEncoder()
    le.fit(classes)

    return le

def getIcdar2013WordList(dataDir, gtFileList):
    wordList = []
    for gtFile in gtFileList:
        try: # val set has comma-separation, train set is just spaces
            df = pd.read_csv(dataDir + '/' +gtFile, delim_whitespace=True,
                            names=('x1','y1','x2','y2','word'))
            area = (df['x2'] - df['x1']) * (df['y2'] - df['y1'])
        except:
            df = pd.read_csv(dataDir + '/' +gtFile,
                            names=('x1','y1','x2','y2','word'))
            area = (df['x2'] - df['x1']) * (df['y2'] - df['y1'])

        # use largest word as search string
        word = df[area == area.max()]['word'].iloc[0]

        # strip nonalphanumeric characters
        word = re.sub('[\W]', '', word)

        # truncate to no more than MAX_L chars
        word = word[:MAX_L]

        wordList.append(word)

    return wordList

def wordsToChars(wordList):
    """Return length and character list of all words in wordList

    Inputs:
        wordList - list of words having length <= MAX_L

    Returns:
        (lenList, charList)
            lenList - list of word lengths
            charMat - (Nwords, MAX_L) ndarray with chars
    """

    lenList = np.zeros(len(wordList), dtype='int8')

    charMat = np.empty((len(wordList), MAX_L), dtype='S1')
    charMat[:] = ''

    for ii,word in enumerate(wordList):
        # Get word length
        lenList[ii] = len(word)

        # Split word in chars to get separate labels for each NN
        charList = list(word)

        # Append empty chars if word is shorter than MAX_L
        charList.extend(np.repeat('', MAX_L - lenList[ii]))
        charMat[ii] = charList

    return (lenList, charMat)

def convertIcdar2013Localization(dataDir, outPrefix, imgExt='jpg',
                                 gtPrefix='gt_', gtExt='txt'):
    """Get list of images and labels for icdar2013 localization dataset

    Goal is to produce files like train.txt and val.txt used in Caffe
    imagenet_training example. Files contain one filename per line followed by
    integer label. We'll produce N_NETS versions of these files since each net
    has a different label corresponding to the different characters in the
    sequence (or the length of the sequence).
    """

    imgFileList = [ff for ff in os.listdir(dataDir)
                   if re.search('.'+imgExt+'$', ff)]
    gtFileList = [ff for ff in os.listdir(dataDir)
                  if re.search('^'+gtPrefix+'\w*.'+gtExt+'$', ff)]
    wordList = getIcdar2013WordList(dataDir, gtFileList)

    lenList, charMat = wordsToChars(wordList)

    # Print training file for length NN
    # here the labels are just 0-MAX_L for the length of the word
    # TO DO - add option for a class that means >MAX_L for longer words
    outFilename = dataDir + '/' + outPrefix + "WordLen.txt"
    with open(outFilename, 'w') as ff:
        lines = ["{} {}\n".format(imgFile, wordLen)
                 for imgFile, wordLen in zip(imgFileList, lenList)]
        ff.writelines(lines)
    print "Wrote " + outFilename
        
    # Print training file for character NNs
    # here the character labels need to be encoded to ints
    le = getLabelEncoder()
    for ii in range(MAX_L):
        outFilename = dataDir + '/' + outPrefix + "Char{}.txt".format(ii)
        with open(outFilename, 'w') as ff:
            lines = ["{} {}\n".format(imgFile, le.transform(charList[ii]))
                     for imgFile, charList in zip(imgFileList, charMat)]
            ff.writelines(lines)
        print "Wrote " + outFilename


def createLevelDB(imgDir, labelFile, outLevelDB):
    """Port of caffe/examples/imagenet/create_imagenet.sh

    Inputs:
        trainDir - name of dir with training images
        trainFile - file with list of image names and labels
        valDir - name of dir with validation images
        valFile - file with list of image names and labels
    """

    toolDir = CAFFE_DIR + "/build/tools"

    print "Creating leveldb..."

    os.system("GLOG_logtostderr=1 {}/convert_imageset.bin {}/ {} " \
        "{}/{} 1".format(toolDir, imgDir, labelFile, LEVELDB_DIR, outLevelDB))

    print "Done creating leveldb."

def computeImageMean(levelDB, outMeanProtoFile):
    """Port of make_imagenet_mean.sh"""
    toolDir = CAFFE_DIR + "/build/tools"
    os.system("{}/compute_image_mean.bin {}/{} {}/{}".format(
        toolDir, LEVELDB_DIR, levelDB, PROTO_DIR, outMeanProtoFile))

def train(prototxtFile):
    """Port of train_imagenet.sh"""
    toolDir = CAFFE_DIR + "/build/tools"
    os.system("GLOG_logtostderr=1 {}/train_net.bin {}".format(toolDir,
                                                              prototxtFile))

def svtXML(xmlFile):
    """Parse StreetViewText XML files to get image name list and word list"""
    with open(xmlFile, 'r') as ff:
        xml = ff.read()

    imgFileList = []
    wordList = []

    bs = BeautifulStoneSoup(xml)
    for im in bs.findAll("image"):
        imgFileList.append(im.imagename.string)
        maxArea = 0
        biggestWord = ''
        for trs in im.findAll("taggedrectangles"):
            for tr in trs.findAll("taggedrectangle"):
                word = tr.text
                area = int(tr.attrs[0][1]) * int(tr.attrs[1][1])
                if area > maxArea:
                    maxArea = area
                    biggestWord = word
        wordList.append(biggestWord)

    return (imgFileList, wordList)

if __name__ == "__main__":

    trainDir = "/Users/mgeorge/insight/icdar2013/localization/train"
    valDir = "/Users/mgeorge/insight/icdar2013/localization/test"

    convertIcdar2013Localization(trainDir, "train")
    convertIcdar2013Localization(valDir, "val")

#    for name in ("Char0", "Char1", "Char2", "WordLen"):
    for name in ("Char0",):

        trainLevelDB = "icdar2013_{}_train_leveldb_short".format(name)
        valLevelDB = "icdar2013_{}_val_leveldb_short".format(name)

        createLevelDB(trainDir, trainDir + "/train{}.txt".format(name),
                      trainLevelDB)
        createLevelDB(valDir, valDir + "/val{}.txt".format(name), valLevelDB)

        trainMeanProto = "icdar2013_{}_mean_short.binaryproto".format(name)
        computeImageMean(trainLevelDB, trainMeanProto)

        prototxtFile = "/Users/mgeorge/insight/protos/icdar2013_{}_solver_short.prototxt".format(name)
        train(prototxtFile)
