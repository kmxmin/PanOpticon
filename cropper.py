# a python package to detect faces, place bounding boxes around faces
#  and auto crop and scale images of faces.

from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
from mtcnn.mtcnn import MTCNN
from PIL import Image
import numpy as np
from numpy import asarray


def highlight_faces(img_path, faces):

    img = plt.imread(img_path)
    plt.imshow(img)

    ax = plt.gca()

    for face in faces:
        x, y, width, height = face["box"]
        face_border = Rectangle((x,y), width, height, fill=False, color='red')
        ax.add_patch(face_border)

    plt.show()


def extract_face(img: np.ndarray, dim=(160,160), bd_width=30) -> np.ndarray :
    #img = plt.imread(img)
    detector = MTCNN()
    faces = detector.detect_faces(img)

    face_images = []

    for face in faces:
        # extract the bounding box from the requested face
        x1, y1, width, height = face['box']
        x2, y2 = x1 + width, y1 + height

        face_boundary = img[y1-bd_width:y2+bd_width, x1-bd_width:x2+bd_width]

        # resize pixels to the model size
        face_image = Image.fromarray(face_boundary)
        face_image = face_image.resize(dim)
        face_array = asarray(face_image)
        face_images.append(face_array)

    return face_images[0]

