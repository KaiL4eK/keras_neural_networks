#! /usr/bin/env python

# Append library path
import sys
sys.path.append('ext_repos/keras-yolo2')

from preprocessing import parse_annotation, parse_annotation_csv
from frontend import YOLO
from datetime import datetime
import numpy as np
import tensorflow as tf
import shutil
import json
import keras
import argparse
import os



os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"]="0"

argparser = argparse.ArgumentParser(
    description='Train and validate YOLO_v2 model on any dataset')

argparser.add_argument(
    '-c',
    '--conf',
    default='config.json',
    help='path to configuration file')


def get_session():
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    return tf.Session(config=config)


def _main_(args):
    config_path = args.conf
    
    keras.backend.tensorflow_backend.set_session(get_session())

    with open(config_path) as config_buffer:    
        config = json.loads(config_buffer.read())

    if config['parser_annotation_type'] == 'xml':
        # parse annotations of the training set
        train_imgs, train_labels = parse_annotation(config['train']['train_annot_folder'], 
                                                    config['train']['train_image_folder'], 
                                                    config['model']['labels'])

        # parse annotations of the validation set, if any, otherwise split the training set
        if os.path.exists(config['valid']['valid_annot_folder']):
            valid_imgs, valid_labels = parse_annotation(config['valid']['valid_annot_folder'], 
                                                        config['valid']['valid_image_folder'], 
                                                        config['model']['labels'])
            split = False
        else:
            split = True
    elif config['parser_annotation_type'] == 'csv':
        # parse annotations of the training set
        train_imgs, train_labels = parse_annotation_csv(config['train']['train_csv_file'],
                                                        config['model']['labels'],
                                                        config['train']['train_csv_base_path'])

        # parse annotations of the validation set, if any, otherwise split the training set
        if os.path.exists(config['valid']['valid_csv_file']):
            valid_imgs, valid_labels = parse_annotation_csv(config['valid']['valid_csv_file'],
                                                        config['model']['labels'],
                                                        config['valid']['valid_csv_base_path'])
            split = False
        else:
            split = True
    else:
        raise ValueError("'parser_annotations_type' must be 'xml' or 'csv' not {}.".format(config['parser_annotations_type']))

    
    if split:
        train_valid_split = int(0.8*len(train_imgs))
        np.random.shuffle(train_imgs)

        valid_imgs = train_imgs[train_valid_split:]
        train_imgs = train_imgs[:train_valid_split]

    if len(config['model']['labels']) > 0:
        overlap_labels = set(config['model']['labels']).intersection(set(train_labels.keys()))

        print('Seen labels:\t', train_labels)
        print('Given labels:\t', config['model']['labels'])
        print('Overlap labels:\t', overlap_labels)           

        if len(overlap_labels) < len(config['model']['labels']):
            print('Some labels have no annotations! Please revise the list of labels in the config.json file!')
            return
    else:
        print('No labels are provided. Train on all seen labels.')
        print('Seen labels:\t', train_labels)
        config['model']['labels'] = train_labels.keys()
        with open("labels.json", 'w') as outfile:
            json.dump({"labels" : list(train_labels.keys())},outfile)

    ###############################
    #   Construct the model 
    ###############################

    yolo = YOLO(backend             = config['model']['backend'],
                input_size          = (config['model']['input_size_h'], config['model']['input_size_w']), 
                labels              = config['model']['labels'], 
                max_box_per_image   = config['model']['max_box_per_image'],
                anchors             = config['model']['anchors'],
                gray_mode           = config['model']['gray_mode'])

    ###############################
    #   Load the pretrained weights (if any) 
    ###############################    

    if os.path.exists(config['train']['pretrained_weights']):
        print("Loading pre-trained weights in", config['train']['pretrained_weights'])
        try:
            yolo.load_weights(config['train']['pretrained_weights'])
        except:
            print("Failed to load pretrained weights")
            print("Continue from scratch!")

    ###############################
    #   Start the training process 
    ###############################

    tensorboard_log_dir_prefix = config['train']['tensorboard_log_dir']
    tensorboard_log_dir_idx = 0
    while True:

        tensorboard_log_dir = tensorboard_log_dir_prefix + '-{}'.format(tensorboard_log_dir_idx)

        if not os.path.exists( tensorboard_log_dir ): 
            print('Set Tensorboard log dir:', tensorboard_log_dir)
            break

        tensorboard_log_dir_idx += 1

    yolo.train(train_imgs         = train_imgs,
               valid_imgs         = valid_imgs,
               train_times        = config['train']['train_times'],
               valid_times        = config['valid']['valid_times'],
               nb_epochs          = config['train']['nb_epochs'], 
               learning_rate      = config['train']['learning_rate'], 
               batch_size         = config['train']['batch_size'],
               warmup_epochs      = config['train']['warmup_epochs'],
               object_scale       = config['train']['object_scale'],
               no_object_scale    = config['train']['no_object_scale'],
               coord_scale        = config['train']['coord_scale'],
               class_scale        = config['train']['class_scale'],
               saved_weights_name = config['train']['saved_weights_name'],
               debug              = config['train']['debug'],
               early_stop         = config['train']['early_stop'],
               workers            = config['train']['workers'],
               max_queue_size     = config['train']['max_queue_size'],
               tb_logdir          = tensorboard_log_dir)

if __name__ == '__main__':
    args = argparser.parse_args()
    _main_(args)
