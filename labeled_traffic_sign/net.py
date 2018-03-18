from keras.models import Sequential, Model
from keras.losses import binary_crossentropy, mean_squared_error, hinge
from keras.layers import Input, concatenate, Conv2D, MaxPooling2D, UpSampling2D, ZeroPadding2D, Dropout, Deconv2D, Flatten, Dense
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint
from keras import backend as K
from keras.utils.layer_utils import print_summary
from keras.utils.vis_utils import plot_model
import numpy as np
import cv2

import tensorflow as tf

K.set_image_data_format('channels_last')  # TF dimension ordering in this code

nn_img_side = 200

glob_label_list = ['stop', 'pedestrian', 'main_road', 'bus_stop']

# Output is resized, BGR, mean subtracted, [0, 1.] scaled by values
def preprocess_img(img):
	img = cv2.resize(img, (nn_img_side, nn_img_side), interpolation = cv2.INTER_LINEAR)

	clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
	img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
	# img_yuv[:,:,0] = cv2.equalizeHist(img_yuv[:,:,0])
	img_yuv[:,:,0] = clahe.apply(img_yuv[:,:,0])
	img = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
	# img = clahe.apply(img)

	img = img.astype('float32', copy=False)
	img /= 255.

	return img

def get_network_model(lr):

	input = Input(shape=(nn_img_side, nn_img_side, 3))

	conv1 = Conv2D(8,(3,3),activation='elu',padding='same')(input)
	pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)
	drop1 = Dropout(0.25)(pool1)

	conv2 = Conv2D(32,(3,3),activation='elu',padding='same')(drop1)
	pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)
	drop2 = Dropout(0.25)(pool2)

	conv3 = Conv2D(64,(3,3),activation='elu',padding='same')(drop2)
	pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)
	drop3 = Dropout(0.25)(pool3)

	conv4 = Conv2D(128,(3,3),activation='elu',padding='same')(drop3)
	drop4 = Dropout(0.25)(conv4)

	flat1  = Flatten()(drop3)
	flat2  = Flatten()(drop4)

	flat   = concatenate([flat1, flat2])

	fc_cls      = Dense(64, activation='tanh')(flat)
	drop_fc_cls = Dropout(0.5)(fc_cls)
	out_cls     = Dense(len(glob_label_list), activation='sigmoid', name='out_cls')(drop_fc_cls)

	model = Model(input, out_cls)
	model.compile(optimizer=Adam(lr=lr), loss='binary_crossentropy', metrics=[])

	print_summary(model)
	plot_model(model, show_shapes=True)

	return model	