import cv2
import camera
import sys

from camera import Camera
from admin_window import admin_window


FD_MODEL_PATH = "model/face_detection_yunet_2023mar.onnx"
FR_MODEL_PATH = "model/face_recognition_sface_2021dec.onnx"


def main(args: list[str]):
    """
    Main function using command line arguments.
        No arguments -> runs a camera window with the 'first' camera connected to this computer.
        a            -> runs a administrative window.
        h            -> used to detect the number of cameras connected to this computer.
                        Each number corresponds to a camera 0-n
        0-n          -> a numeric value ranging from opening a camera window on that camera
    """

    if len(args) == 1:
        # no arguments. Run camera window on first camera connected to computer
        camera_obj = Camera(FD_MODEL_PATH, FR_MODEL_PATH, camera=0)
        camera_obj.camera_loop()

    elif len(args) == 2:

        if args[1] == "a":
            # run admin.
            admin_obj = admin_window(FD_MODEL_PATH, FR_MODEL_PATH)

        elif args[1] == "h":
            # check number of cameras and print to terminal

            cameras = camera.get_avail_cameras()
            print(cameras)

        elif args[1].isnumeric:
            # run camera window on specific camera

            camera_id = int(args[1])
            camera_obj = Camera(FD_MODEL_PATH, FR_MODEL_PATH, camera=camera_id)
            camera_obj.camera_loop()

    print("good bye ;)")


if __name__ == "__main__":
    # run main function

    args = sys.argv
    main(args)
