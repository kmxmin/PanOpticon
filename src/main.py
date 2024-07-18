
import cv2
import camera
import sys

from camera import Camera
from admin_window import admin_window

import image_tools

FD_MODEL_PATH = "model/face_detection_yunet_2023mar.onnx"
FR_MODEL_PATH = "model/face_recognition_sface_2021dec.onnx"

def main(args: list[str]): 

    if len(args) == 1:
        camera_obj0 = Camera(FD_MODEL_PATH, FR_MODEL_PATH, camera=0)
        camera_obj0.camera_loop()

    elif len(args) == 2:

        if args[1] == "a":
            # run admin
            admin_obj = admin_window(FD_MODEL_PATH, FR_MODEL_PATH)
        
        elif args[1] == "h":
            cameras = camera.get_avail_cameras()
            print(cameras)

        elif args[1].isnumeric:
            camera_id = int(args[1])
            camera_obj0 = Camera(FD_MODEL_PATH, FR_MODEL_PATH, camera=camera_id)
            camera_obj0.camera_loop()

    print("good bye ;)")


if __name__ == "__main__":
    args = sys.argv
    
    main(args)