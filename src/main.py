
import cv2

from camera import Camera
from admin_window import admin_window
from yunet import YuNet

import image_tools

FD_MODEL_PATH = "model/face_detection_yunet_2023mar.onnx"
FR_MODEL_PATH = "model/face_recognition_sface_2021dec.onnx"

def main():

    # admin_obj = admin_window()

    # camera_obj = Camera(FD_MODEL_PATH, FR_MODEL_PATH)
    # camera_obj.camera_loop()

    src_img = cv2.imread("src/test.jpg")

    fd_model.setInputSize([src_img.shape[1], src_img.shape[0]])

    img, num_faces = image_tools.extract_face(src_img, fd_model)

    print(img)

    cv2.imshow(f"numfaces {num_faces}", img)
    cv2.imwrite("out.jpg", img)

if __name__ == "__main__":
    main()