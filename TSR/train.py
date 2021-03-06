import os
import pandas as pd
import models
import data
import generator as gen
import json
from tensorflow.keras.optimizers import Adam

from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint

import multiprocessing

from _common import utils
from _common import callbacks as cbs

import argparse

argparser = argparse.ArgumentParser(description='train and evaluate YOLOv3 model on any dataset')
argparser.add_argument('-c', '--conf', help='path to configuration file')
argparser.add_argument('-w', '--weights', help='path to trained model', default=None)

args = argparser.parse_args()

import neptune
neptune.init('kail4ek/sandbox')

def main():
    config_path = args.conf
    initial_weights = args.weights

    with open(config_path) as config_buffer:
        config = json.loads(config_buffer.read())

    train_set, valid_set, classes = data.create_training_instances(config['train']['train_folder'],
                                                                   None,
                                                                   config['train']['cache_name'],
                                                                   config['model']['labels'])

    num_classes = len(classes)
    print('Readed {} classes: {}'.format(num_classes, classes))

    train_generator = gen.BatchGenerator(
        instances=train_set,
        labels=classes,
        batch_size=config['train']['batch_size'],
        input_sz=config['model']['infer_shape'],
        shuffle=True,
        norm=data.normalize
    )

    valid_generator = gen.BatchGenerator(
        instances=valid_set,
        labels=classes,
        batch_size=config['train']['batch_size'],
        input_sz=config['model']['infer_shape'],
        norm=data.normalize,
        infer=True
    )

    early_stop = EarlyStopping(
        monitor='val_loss',
        min_delta=0,
        patience=20,
        mode='min',
        verbose=1
    )

    reduce_on_plateau = ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=5,
        verbose=1,
        mode='min',
        min_delta=0.01,
        cooldown=0,
        min_lr=0
    )

    net_input_shape = (config['model']['infer_shape'][0],
                       config['model']['infer_shape'][1],
                       3)

    train_model = models.create(
        base_name=config['model']['base'],
        num_classes=num_classes,
        input_shape=net_input_shape)

    if initial_weights:
        train_model.load_weights(initial_weights)

    print(train_model.summary())
    # plot_model(train_model, to_file='images/MobileNetv2.png', show_shapes=True)

    optimizer = Adam(lr=config['train']['learning_rate'], clipnorm=0.001)

    train_model.compile(loss='categorical_crossentropy', optimizer=optimizer, metrics=['accuracy'])

    checkpoint_name = utils.get_checkpoint_name(config)
    utils.makedirs_4_file(checkpoint_name)

    static_chk_name = utils.get_static_checkpoint_name(config)
    utils.makedirs_4_file(static_chk_name)

    checkpoint_vloss = cbs.CustomModelCheckpoint(
        model_to_save=train_model,
        filepath=checkpoint_name,
        monitor='val_loss',
        verbose=1,
        save_best_only=True,
        mode='min',
        period=1
    )
    
    neptune_mon = cbs.NeptuneMonitor(
        monitoring=['loss', 'val_loss', 'accuracy', 'val_accuracy'],
        neptune=neptune
    )

    chk_static = ModelCheckpoint(
        filepath=static_chk_name,
        monitor='val_loss',
        verbose=1,
        save_best_only=True,
        mode='min',
        period=1
    )

    callbacks = [early_stop, reduce_on_plateau, checkpoint_vloss, neptune_mon, chk_static]

    ### NEPTUNE ###
    sources_to_upload = [
        'models.py',
        'config.json'
    ]

    params = {
        'infer_size': "H{}xW{}".format(*config['model']['infer_shape']),
        'classes': config['model']['labels'],
    }

    neptune.create_experiment(
        name=utils.get_neptune_name(config),
        upload_stdout=False,
        upload_source_files=sources_to_upload,
        params=params
    )
    ### NEPTUNE ###
    
    hist = train_model.fit_generator(
        generator=train_generator,
        steps_per_epoch=len(train_generator) * config['train']['train_times'],

        validation_data=valid_generator,
        validation_steps=len(valid_generator) * config['valid']['valid_times'],

        epochs=config['train']['nb_epochs'],
        verbose=2 if config['train']['debug'] else 1,
        callbacks=callbacks,
        workers=multiprocessing.cpu_count(),
        max_queue_size=100
    )
    
    neptune.send_artifact(static_chk_name)
    neptune.send_artifact('config.json')

    # Hand-made history
    # if not os.path.exists('model'):
    #     os.makedirs('model')

    # df = pd.DataFrame.from_dict(hist.history)
    # df.to_csv('model/hist.csv', encoding='utf-8', index=False)


if __name__ == '__main__':
    main()
