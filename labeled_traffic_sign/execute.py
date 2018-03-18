from __future__ import print_function

import matplotlib.pyplot as plt 
import matplotlib.animation as animation

import os
import cv2
import numpy as np
import time
from keras.models import Model, load_model, save_model

from net import *
import argparse

# from skvideo.io import VideoCapture

parser = argparse.ArgumentParser(description='Process video with ANN')
parser.add_argument('weights', action='store', help='Path to weights file')
parser.add_argument('filepath', action='store', help='Path to video file to process')
parser.add_argument('-f', '--fps', action='store_true', help='Check fps')
parser.add_argument('-p', '--pic', action='store_true', help='Process picture')
parser.add_argument('-n', '--negative', action='store_true', help='Negative creation')
# parser.add_argument('-g', '--gif', action='store_true', help='Create gif')

args = parser.parse_args()

data_path = 'raw/'

try:
	xrange
except NameError:
	xrange = range

def process_naming(frame, model):

	img_class = model.predict(np.array([preprocess_img(frame)]))[0]
	
	thresshold = .8
	class_active = [ class_list[index] for index, value in enumerate(img_class) if value > thresshold ]

	for i, class_ in enumerate(class_active):
		# print(class_)
		font = cv2.FONT_HERSHEY_SIMPLEX
		cv2.putText(frame, class_, (10, (i+1)*50), font, 1.5, (255, 0, 0), 3)

	return frame

def get_next_negative_id():
	maximum_id = 0

	data_path = '../negative'
	images = os.listdir(data_path)

	for imagefile in images:
		info   = imagefile.split(';')
		maximum_id = max(maximum_id, int(info[0]))

	return maximum_id+1

def execute_model():
	model = get_network_model()

	print('-'*30)
	print('Loading weights file: {}'.format(args.weights))
	print('-'*30)

	model.load_weights(args.weights)

	print('-'*30)
	print('Network initialized')
	print('-'*30)

	if args.pic:
		frame = cv2.imread(args.filepath)
		if frame is None:
			print('Failed to open file')
			exit(1)

		process_naming(frame, model)

		cv2.imshow('frame',frame)
		cv2.waitKey(0)
		exit(1)
	else:
		print('-'*30)
		print('Processing videofile: %s' % args.filepath)
		print('-'*30)

		cap = cv2.VideoCapture(args.filepath)
		if cap is None or not cap.isOpened():
			print('Failed to open file')
			exit(1)

		ret, frame = cap.read()
		if frame is None:
			print('Failed to read frame')
			exit(1)

		if args.fps:
			bbox_obtain_time = 0
			num_frames = 120
			start = time.time()
			for i in xrange(0, num_frames) :
				ret, frame = cap.read()
				if frame is None:
					exit(1)

				start_bbox = time.time()

				process_naming(frame, model)
				
				cv2.imshow('frame',frame)
				if cv2.waitKey(1) & 0xFF == ord('q'):
					break

			seconds = time.time() - start
			print('Mean time per frame : {0} ms'.format(seconds / num_frames * 1000))
			print('Estimated frames per second : {0}'.format(num_frames / seconds))
			print('Bbox obtain mean time : {0} ms'.format(bbox_obtain_time / num_frames * 1000))

		elif args.negative:	
			negative_id = get_next_negative_id()
			while(cap.isOpened()):
				ret, frame = cap.read()
				if frame is None:
					exit(1)

				process_naming(frame, model)
				
				cv2.imshow('frame',frame)

				wait_res = cv2.waitKey(0)
				if wait_res & 0xFF == ord(' '):
					filename = '../negative/{};0;0;0;0;neg.png'.format(negative_id)
					print('Saving to file: {}'.format(filename))
					negative_id += 1

					cv2.imwrite(filename, frame)

				if wait_res & 0xFF == ord('q'):
					break
		else:
			while(cap.isOpened()):
				ret, frame = cap.read()
				if frame is None:
					exit(1)

				process_naming(frame, model)

				cv2.imshow('frame',frame)
				if cv2.waitKey(1) & 0xFF == ord('q'):
					break

				frame = cv2.resize(frame, (80, 80), interpolation = cv2.INTER_LINEAR)

		cap.release()
		cv2.destroyAllWindows()

if __name__ == '__main__':
	execute_model()