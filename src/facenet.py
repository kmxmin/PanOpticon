# facenet encoder and verification module
# from kaggle project https://www.kaggle.com/code/joshuabritz/face-verification-and-recognition/edit

import keras
import numpy as np
from matplotlib import pyplot as plt
import cropper
from tensorflow import subtract
import cv2

def load_model(model_path):
    layer = keras.layers.TFSMLayer(model_path, call_endpoint="serving_default")
    model = keras.Sequential([layer])

    print("model loaded...")

    return model


# checks if the image is too bright/dark
def brightness_check(img : np.ndarray): 
    brightness = np.mean(img)

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



def img_to_encoding(img: np.ndarray, model):
    # img = keras.preprocessing.image.load_img(img_path, target_size=(160, 160))
    # cropping first face seen

    img = cropper.extract_face(img)
    img = np.around(np.array(img) / 255.0, decimals=12)

    
    x_train = np.expand_dims(img, axis=0) # add a dimension of 1 as first dimension
    embedding = model.predict_on_batch(x_train)
    mag = np.linalg.norm(embedding["Bottleneck_BatchNorm"][0])
    return embedding["Bottleneck_BatchNorm"] / mag



def save_face(img_path: str, name: str, Database, model: keras.Model):
    # save to vector database...?
    # crop and then encode

    img = plt.imread(img_path)
    img = cropper.extract_face(img)

    encoding = img_to_encoding(img, model)

    Database[name] = encoding

'''
def verify(img_path: str, identity: str, database, model: keras.Model, threshold=0.7):
    # performs facial verification by querying the db.
    
    img = plt.imread(img_path)
    img = cropper.extract_face(img)

    plt.imshow(img)
    plt.show()

    encoding = img_to_encoding(img, model)
    dist = np.linalg.norm(subtract(database[identity], encoding))

    if dist < threshold:
        print("It's " + str(identity) + ", welcome in!")
        door_open = True
    else:
        print("It's not " + str(identity) + ", please go away")
        door_open = False
    return dist, door_open
'''
