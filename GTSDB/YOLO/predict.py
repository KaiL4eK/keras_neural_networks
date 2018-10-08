#! /usr/bin/env python

import argparse
import os
import cv2
import numpy as np
from tqdm import tqdm
from utils import draw_boxes
from frontend import YOLO
from utils import list_images
import json
import tensorflow as tf
import common as cmn
import keras.backend as K

os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"]="0"

def init_session():
    config = tf.ConfigProto()

    config.gpu_options.allow_growth                     = True
    config.gpu_options.per_process_gpu_memory_fraction  = 0.5

    if cmn.isDataFormatCv():
        print('Data format: HWC')
    else:
        print('Data format: CWH')

    K.set_session(tf.Session(config=config))

argparser = argparse.ArgumentParser(
    description='Train and validate YOLO_v2 model on any dataset')

argparser.add_argument(
    '-c',
    '--conf',
    default='config.json',
    help='path to configuration file')

argparser.add_argument(
    '-w',
    '--weights',
    default='',
    help='path to pretrained weights')

argparser.add_argument(
    '-i',
    '--input',
    help='path to an image or an video (mp4 format)')


def _main_(args):
    config_path  = args.conf
    weights_path = args.weights
    image_path   = args.input

    init_session()

    with open(config_path) as config_buffer:    
        config = json.load(config_buffer)

    if weights_path == '':
        weights_path = config['train']['saved_weights_name']

    ###############################
    #   Make the model 
    ###############################

    yolo = YOLO(backend             = config['model']['backend'],
                input_size          = (config['model']['input_size_h'],config['model']['input_size_w']), 
                labels              = config['model']['labels'], 
                max_box_per_image   = config['model']['max_box_per_image'],
                anchors             = config['model']['anchors'],
                gray_mode           = config['model']['gray_mode'])

    ###############################
    #   Load trained weights
    ###############################    

    yolo.load_weights(weights_path)

    ###############################
    #   Predict bounding boxes 
    ###############################

    if image_path[-4:] == '.mp4':
        video_out = image_path[:-4] + '_detected' + image_path[-4:]
        video_reader = cv2.VideoCapture(image_path)

        nb_frames = int(video_reader.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_h = int(video_reader.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_w = int(video_reader.get(cv2.CAP_PROP_FRAME_WIDTH))

        video_writer = cv2.VideoWriter(video_out,
                               cv2.VideoWriter_fourcc(*'MPEG'), 
                               50.0, 
                               (frame_w, frame_h))

        nb_frames = min(nb_frames, 200)

        for i in tqdm(range(nb_frames)):
            _, image = video_reader.read()
            
            boxes = yolo.predict(image)
            image = draw_boxes(image, boxes, config['model']['labels'])

            video_writer.write(np.uint8(image))

        video_reader.release()
        video_writer.release()  
    else:
        if os.path.isfile(image_path):
            image = cv2.imread(image_path)
            boxes = yolo.predict(image)
            image = draw_boxes(image, boxes, config['model']['labels'])

            print(len(boxes), 'boxes are found')

            cv2.imwrite(image_path[:-4] + '_detected' + image_path[-4:], image)
        else:
            detected_images_path = os.path.join(image_path, "detected")
            if not os.path.exists(detected_images_path):
                os.mkdir(detected_images_path)
            images = list(list_images(image_path))
            for fname in tqdm(images):
                image = cv2.imread(fname)
                boxes = yolo.predict(image)
                image = draw_boxes(image, boxes, config['model']['labels'])
                fname = os.path.basename(fname)
                cv2.imwrite(os.path.join(image_path, "detected", fname), image)

if __name__ == '__main__':
    args = argparser.parse_args()
    _main_(args)
