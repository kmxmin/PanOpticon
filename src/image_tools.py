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

    return output, len(results)