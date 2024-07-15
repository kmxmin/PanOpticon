
import cv2
import numpy as np
import os.path

from camera import Camera

FD_MODEL_PATH = "model/face_detection_yunet_2023mar.onnx"
FR_MODEL_PATH = "model/face_recognition_sface_2021dec.onnx"

def main():

    camera_obj = Camera(FD_MODEL_PATH, FR_MODEL_PATH)
    camera_obj.camera_loop()

if __name__ == "__main__":
    main()