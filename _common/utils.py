import os
import cv2


def get_impaths_from_path(path):

    image_paths = []

    if os.path.isdir(path):
        for root, subdirs, files in os.walk(path):
            pic_extensions = ('.png', '.PNG', '.jpg', 'JPEG', '.ppm')
            image_paths += [os.path.join(root, file) for file in files if file.endswith(pic_extensions)]
    else:
        image_paths += [path]

    return image_paths


def data_generator(input_path):
    video_extensions = ('.mp4', '.webm', '.mov')

    if '/dev/video' in input_path: # do detection on the first webcam
        video_reader = cv2.VideoCapture(input_path)

        while True:
            ret_val, image = video_reader.read()

            yield image
        
    elif input_path.endswith(video_extensions):
        video_reader = cv2.VideoCapture(input_path)

        while True:
            ret_val, image = video_reader.read()

            yield image

    else: # do detection on an image or a set of images
        image_paths = get_impaths_from_path(input_path)

        # the main loop
        for image_path in image_paths:
            image = cv2.imread(image_path)
            
            yield image


def makedirs(dirpath):
    if not os.path.isdir(dirpath):
        # Not exist
        os.makedirs(dirpath)


def makedirs_4_file(filepath):
    dirpath = os.path.dirname(filepath)
    makedirs(dirpath)
