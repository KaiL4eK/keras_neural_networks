#!/bin/bash

if [ -z "$MO_PATH" ]
then
      echo "\$MO_PATH is not set / OpenVINO env not set"
      exit
fi

GRAPH_PATH=$1
INPUT_SHAPE="[2,416,416,3]"
OUTPUT_DIR="models"

OPTIM_DIR="for_optimization"

mkdir -p $OPTIM_DIR; cp $GRAPH_PATH $OPTIM_DIR;
GRAPH_FNAME=`basename $GRAPH_PATH`

echo "Optimizing $GRAPH_FNAME"

python $MO_PATH --input_model $OPTIM_DIR/$GRAPH_FNAME --scale 255 --input_shape $INPUT_SHAPE --output_dir $OUTPUT_DIR --data_type FP16

# --model_name '$OUTPUT_MODEL'_fp32
#  --log_level=DEBUG
