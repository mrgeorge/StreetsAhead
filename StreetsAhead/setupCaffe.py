import os

CAFFE_DIR = "/Users/mgeorge/insight/caffe"
LEVELDB_DIR = "/Users/mgeorge/insight/leveldbs"
PROTO_DIR = "/Users/mgeorge/insight/protos"

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
    os.system("GLOG_logtostderr=1 {}/compute_image_mean.bin {}/{} {}/{}".format(
        toolDir, LEVELDB_DIR, levelDB, PROTO_DIR, outMeanProtoFile))

def train(prototxtFile):
    """Port of train_imagenet.sh"""
    toolDir = CAFFE_DIR + "/build/tools"
    os.system("GLOG_logtostderr=1 {}/train_net.bin {}".format(toolDir,
                                                              prototxtFile))

if __name__ == "__main__":

    trainDir = "/Users/mgeorge/insight/masterTrainData"
    valDir = "/Users/mgeorge/insight/masterValData"

    #    objectives = ("Char0", "Char1", "Char2", "WordLen")
    objectives = ("Char0",)

    for obj in objectives:
        print obj
        print "creating leveldb"
        trainLevelDB = "master_{}_train_leveldb_short".format(obj)
        valLevelDB = "master_{}_val_leveldb_short".format(obj)

        createLevelDB(trainDir, trainDir + "/train{}.txt".format(obj),
                      trainLevelDB)
        createLevelDB(valDir, valDir + "/val{}.txt".format(obj), valLevelDB)

        print "computing image mean"
        trainMeanProto = "master_{}_mean_short.binaryproto".format(obj)
        computeImageMean(trainLevelDB, trainMeanProto)

        print "training"
        prototxtFile = "/Users/mgeorge/insight/protos/" \
            "master_{}_solver_short.prototxt".format(obj)
        train(prototxtFile)
