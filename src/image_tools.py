# image tools for calculating embeddings and cropping to faces

import cv2
import numpy as np

from sface import SFace
from yunet import YuNet


def image_to_encoding(img: np.ndarray, model: SFace):
    return model.infer(image=img)


def image_to_encoding(img: np.ndarray, bbox, model: SFace):
    return model.infer(image=img, bbox=bbox)


def extract_face(img: np.ndarray, model: YuNet, buffer=20):
    # returns a cropped image using YuNet

    results = model.infer(img)
    buffer_hlf = buffer//2

    if len(results) > 0: 
        face = results[0]
        bbox = face[0:4].astype(np.int32)
 
        x1, y1 = bbox[0]-buffer_hlf, bbox[1]-buffer_hlf
        x2, y2 = bbox[0] + bbox[2] + buffer_hlf, bbox[1] + bbox[3] + buffer_hlf

        output = img[y1:y2, x1:x2]
        cv2.resize(output, (160, 160))

    return output, len(results)


# checks if the image is too bright/dark
def brightness_check(img : np.ndarray): 
    brightness = np.mean(img)
    print("Brightness: " + str(brightness))

    return brightness


# gamma correction of images that are too bright/dark
def adjust_gamma(img : np.ndarray, gamma : float):

    # build a LUT mapping the pixel values [0, 255] to their adjusted gamma values
    if img.dtype != np.uint8:
        img = img.astype(np.uint8)

    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255
        for i in np.arange(0, 256)]).astype("uint8")

    return cv2.LUT(img, table)
