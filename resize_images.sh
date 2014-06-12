#!/usr/bin/env sh

# copy images to a subfolder 256x256 and resize
# See http://caffe.berkeleyvision.org/imagenet_training.html for context

args=("$@")

DATADIR=${args[0]}

mkdir $DATADIR/full_res
cp $DATADIR/*.jpg $DATADIR/full_res
for name in $DATADIR/*.jpg; do
    convert -resize 256x256\! $name $name
done
