import os
import string
import re

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from BeautifulSoup import BeautifulStoneSoup

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

def makeLabelFiles(objectives, dataDir, imgFileList, lenList, charMat):
    # Print training file for length NN
    # here the labels depend on objectives
    #    just 0-MAX_L for the length of the word
    # TO DO - add option for a class that means >MAX_L for longer words
    outFilenames = []
    for obj in objectives:
        outFilename = dataDir + '/' + outPrefix + "{}.txt".format(obj)
        outFilenames.append(outFilename)

        if obj == "WordLen"
            with open(outFilename, 'w') as ff:
                lines = ["{} {}\n".format(imgFile, wordLen)
                        for imgFile, wordLen in zip(imgFileList, lenList)]
            ff.writelines(lines)
        else:
            # Print training file for character NNs
            ii = int(obj[-1]) # expects obj to be form 'Char0' or 'Char1'

            # here the character labels need to be encoded to ints
            le = getLabelEncoder()
            with open(outFilename, 'w') as ff:
                lines = ["{} {}\n".format(imgFile, le.transform(charList[ii]))
                        for imgFile, charList in zip(imgFileList, charMat)]
            ff.writelines(lines)

        print "Wrote " + outFilename

    return outFilenames

def convertIcdar2013Localization(dataDir, outPrefix, objectives, imgExt='jpg',
                                 gtPrefix='gt_', gtExt='txt'):
    """Get list of images and labels for icdar2013 localization dataset

    Goal is to produce files like train.txt and val.txt used in Caffe
    imagenet_training example. Files contain one filename per line followed by
    integer label. We'll produce N_NETS versions of these files since each net
    has a different label corresponding to the different characters in the
    sequence (or the length of the sequence).

    Returns:
        outFilenames - list of files, one for each objective with image name
                       and label, one per line
    """

    imgFileList = [ff for ff in os.listdir(dataDir)
                   if re.search('.'+imgExt+'$', ff)]
    gtFileList = [ff for ff in os.listdir(dataDir)
                  if re.search('^'+gtPrefix+'\w*.'+gtExt+'$', ff)]
    wordList = getIcdar2013WordList(dataDir, gtFileList)

    lenList, charMat = wordsToChars(wordList)
    outFilenames = makeLabelFiles(objectives, dataDir, imgFileList, lenList,
                                  charMat)
    return outFilenames

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
                area = int(tr.attrs[0][1]) * int(tr.attrs[1][1]) # height*width
                if area > maxArea:
                    maxArea = area
                    biggestWord = word
        wordList.append(biggestWord)

    return (imgFileList, wordList)

def convertSVT(svtDir, svtXMLFile, objectives):
    """Get list of images and labels for StreetView Text dataset

    Goal is to produce files like train.txt and val.txt used in Caffe
    imagenet_training example. Files contain one filename per line followed by
    integer label. We'll produce N_NETS versions of these files since each net
    has a different label corresponding to the different characters in the
    sequence (or the length of the sequence).

    Returns:
        outFilenames - list of files, one for each objective with image name
                       and label, one per line
    """

    imgFileList, wordList = svtXML(svtXMLFile)
    lenList, charMat = wordsToChars(wordList)
    outFilenames = makeLabelFiles(objectives, svtDir, imgFileList, lenList,
                                  charMat)
    return outFilenames

if __name__ == "__main__":

#    objectives = ("Char0", "Char1", "Char2", "WordLen")
    objectives = ("Char0",)

    icdarTrainDir = "/Users/mgeorge/insight/icdar2013/localization/train"
    icdarValDir = "/Users/mgeorge/insight/icdar2013/localization/test"

    icdarTrainLabelFiles = convertIcdar2013Localization(icdarTrainDir, "train")
    icdarValLabelFiles = convertIcdar2013Localization(icdarValDir, "val")

    svtDir = "/Users/mgeorge/insight/streetview_text/data"
    # Note: I'm switching the train and test sets since test is larger
    svtTrainXML = svtDir + "/test.xml"
    svtValXML = svtDir + "/train.xml"

    svtTrainLabelFiles
