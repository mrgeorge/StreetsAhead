import os
import string
import re
import shutil

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from BeautifulSoup import BeautifulStoneSoup
import skimage.io, skimage.transform

MAX_L = 5 # longest string to look for
N_NETS = MAX_L + 1 # one network for each char + one for length fig 12 1312.6082

def getLabelEncoder():
    """Define A-Z, a-z, 0-9, '' as classes and encode to integers"""
    classes = list(string.letters + string.digits)
    classes.append('')
    le = LabelEncoder()
    le.fit(classes)

    return le

def cleanWord(word):
    # strip nonalphanumeric characters
    word = re.sub('[\W]', '', word)
    # truncate to no more than MAX_L chars
    word = word[:MAX_L]

    return word

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

        wordList.append(cleanWord(word))

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

def makeLabelFiles(objectives, imgDir, imgFileList, lenList, charMat,
                   outPrefix):
    """
    Inputs:
        objectives - tuple of strings, e.g. ("Char0", "WordLen")
        imgDir - dir where images live and where output label file will go
        imgFileList - list of image names (no paths)
        lenList - list of word lengths
        charMat - 2d array nWords x nChars with word splits

    Returns:
        outFilenames - list of output files with image name + label, one per line
        (also these files are created and written)
    """

    # Print training file for length NN
    # here the labels depend on objectives
    #    just 0-MAX_L for the length of the word
    # TO DO - add option for a class that means >MAX_L for longer words
    outFilenames = []
    for obj in objectives:
        outFilename = "{}/{}{}.txt".format(imgDir, outPrefix, obj)
        outFilenames.append(outFilename)

        if obj == "WordLen":
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
                                  charMat, outPrefix)
    return outFilenames

def svtXML(xmlFile):
    """Parse StreetViewText XML files to get image name list and word list"""
    with open(xmlFile, 'r') as ff:
        xml = ff.read()

    imgFileList = []
    wordList = []

    bs = BeautifulStoneSoup(xml)
    for im in bs.findAll("image"):
        imgFile = im.imagename.string.split('/')[-1] # keep only file name
        imgFileList.append(imgFile)
        maxArea = 0
        biggestWord = ''
        for trs in im.findAll("taggedrectangles"):
            for tr in trs.findAll("taggedrectangle"):
                word = tr.text
                area = int(tr.attrs[0][1]) * int(tr.attrs[1][1]) # height*width
                if area > maxArea:
                    maxArea = area
                    biggestWord = word
        wordList.append(cleanWord(biggestWord))

    return (imgFileList, wordList)

def convertSVT(svtImgDir, svtXMLFile, outPrefix, objectives):
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
    outFilenames = makeLabelFiles(objectives, svtImgDir, imgFileList, lenList,
                                  charMat, outPrefix)
    return outFilenames

def convertChars74K(topDir, chars74KTypes, outPrefix, objectives, imgExt='png'):

    le = getLabelEncoder()
    fullOutfileList = []
    fullImgDirList = []
    for typeDir in chars74KTypes:
        for ii in range(1,63):
            sampleDir = "Sample{:03d}".format(ii)
            fullDir = "{}/{}/{}".format(topDir,typeDir,sampleDir)
            imgFileList = [ff for ff in os.listdir(fullDir)
                           if re.search('.'+imgExt+'$', ff)]
            lenList = [1] * len(imgFileList) # just one char each
            letter = le.inverse_transform(ii)
            charList = [letter]
            charList.extend(np.repeat('', MAX_L - 1))
            charMat = np.tile(charList, (len(imgFileList), 1))

            outFilenames = makeLabelFiles(objectives, fullDir, imgFileList, lenList,
                                          charMat, outPrefix)
            fullOutfileList.extend(outFilenames)
            fullImgDirList.append(fullDir)

    return (fullOutfileList, fullImgDirList)

def makeMasterDataDir(masterDataDir, labelFiles, imgDirs, outPrefix, outScale=256):

    # concatenate label files into master label file
    # copy each image file to master dir
    masterLabelFile = "{}/{}.txt".format(masterDataDir, outPrefix)
    with open(masterLabelFile, 'w') as mlf:
        for labelFile, imgDir, ext in zip(labelFiles, imgDirs, range(len(imgDirs))):
            with open(labelFile, 'r') as lf:
                lfText = lf.read()
                for line in lfText.splitlines():
                    origName, label = line.split(' ')
                    mlf.write("ext{}_{} {}\n".format(ext, origName, label))
                    srcFile = "{}/{}".format(imgDir, origName)

                    img = skimage.io.imread(srcFile)
                    img = skimage.transform.resize(img, (outScale, outScale))
                    skimage.io.imsave("{}/ext{}_{}".format(masterDataDir,ext,origName), img)

    return masterLabelFile

if __name__ == "__main__":

#    objectives = ("Char0", "Char1", "Char2", "WordLen")
    objectives = ("Char0",)
    # TO DO - need to loop over some parts below to get different labels for each objective

    icdarTrainDir = "/Users/mgeorge/insight/icdar2013/localization/train"
    icdarValDir = "/Users/mgeorge/insight/icdar2013/localization/test"

    icdarTrainLabelFiles = convertIcdar2013Localization(icdarTrainDir, "train",
                                                        objectives)
    icdarValLabelFiles = convertIcdar2013Localization(icdarValDir, "val",
                                                      objectives)

    svtImgDir = "/Users/mgeorge/insight/streetview_text/data/img"
    # Note: I'm switching the train and test sets since test is larger
    svtTrainXML = "/Users/mgeorge/insight/streetview_text/data/test.xml"
    svtValXML = "/Users/mgeorge/insight/streetview_text/data/train.xml"

    svtTrainLabelFiles = convertSVT(svtImgDir, svtTrainXML, "train",
                                    objectives)
    svtValLabelFiles = convertSVT(svtImgDir, svtValXML, "val",
                                  objectives)

    chars74KDir = "/Users/mgeorge/insight/chars74k/English"
    chars74KTypes = ["Fnt", "Hnd/Img", "Img/GoodImg/Bmp"] # subdirs with images
    chars74KTrainLabelFiles, chars74KTrainImgDirs = convertChars74K(chars74KDir,
        chars74KTypes, "train", objectives)


    # compile all the label files
    allTrainLabelFiles = []
    allTrainLabelFiles.extend(icdarTrainLabelFiles)
    allTrainLabelFiles.extend(svtTrainLabelFiles)
    allTrainLabelFiles.extend(chars74KTrainLabelFiles)

    allValLabelFiles = []
    allValLabelFiles.extend(icdarValLabelFiles)
    allValLabelFiles.extend(svtTrainLabelFiles)

    # get corresponding image dirs
    allTrainImgDirs = []
    allTrainImgDirs.extend([icdarTrainDir] * len(icdarTrainLabelFiles))
    allTrainImgDirs.extend([svtImgDir] * len(svtTrainLabelFiles))
    allTrainImgDirs.extend(chars74KTrainImgDirs)

    allValImgDirs = []
    allValImgDirs.extend([icdarValDir] * len(icdarValLabelFiles))
    allValImgDirs.extend([svtImgDir] * len(svtValLabelFiles))

    masterTrainDataDir = "/Users/mgeorge/insight/masterTrainData"
    masterValDataDir = "/Users/mgeorge/insight/masterValData"
    masterTrainLabelFile = makeMasterDataDir(masterTrainDataDir,
                                             allTrainLabelFiles,
                                             allTrainImgDirs,
                                             "train")
    masterValLabelFile = makeMasterDataDir(masterValDataDir,
                                           allValLabelFiles,
                                           allValImgDirs,
                                           "val")
