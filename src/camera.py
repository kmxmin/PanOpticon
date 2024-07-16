# handles camera input with realtime(ish) face detection and recognition

import cv2
import numpy as np

from datetime import datetime
from threading import Event

from yunet import YuNet
from sface import SFace

class Camera():
    def __init__(self, fd_model_path: str, fr_model_path: str) -> None:        

        # load in detection and recognition models
        self.fdetect_model = YuNet(modelPath=fd_model_path, confThreshold=0.8)
        self.frecogi_model = SFace(modelPath=fr_model_path, disType=1)
        print("models loaded...")

        self.loadKnownFaces("Path")

        self.vid_stream = cv2.VideoCapture(0)
        self.width = int(self.vid_stream.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.vid_stream.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.is_on = Event()
        self.is_on.clear()

        self.fdetect_model.setInputSize([self.width, self.height])

        self.tm = cv2.TickMeter()

    def camera_loop(self):
        print("camera loop")
        
        self.is_on.set()

        while self.is_on.is_set():

            hasFrame, frame = self.vid_stream.read()

            if not hasFrame:
                print("no frame :(")
                break
            
            elif cv2.waitKey(1) & 0xFF == ord('q'):
                self.vid_stream.release
                break

            self.tm.start()
            fdetect_results = self.fdetect_model.infer(frame)
            self.tm.stop()

            frame = self.visualize(frame, fdetect_results, fps=self.tm.getFPS)

            cv2.imshow("camera", frame)

            self.tm.reset()
    
    def get_name_tag(self, img) -> tuple:
        name_tag = "?unknown?"

        # this_emb = self.frecogi_model.infer(img, bbox)
        this_emb = self.frecogi_model.infer(img)

        for name in self.KnownEmbs:
        
            trg_emb = self.KnownEmbs[name]
            dist, is_recognised = self.frecogi_model.dist(trg_emb, this_emb)

            if is_recognised:
                name_tag = name
        
        return name_tag, dist, is_recognised

    def visualize(self, img, results, box_col=(2,255,255), text_col=(2,255,255), fps=None) -> np.ndarray:
        # adds fps counter and time 
        # adds bounding boxes and name tags

        output = img.copy()

        for i, det in enumerate(results):
            
            name, dist, is_recognised = self.get_name_tag(output)

            if is_recognised:
                bbox = det[0:4].astype(np.int32)
                x1, y1 = bbox[0], bbox[1]
                x2, y2 = bbox[0] + bbox[2], bbox[1] + bbox[3]

                cv2.rectangle(output, (x1, y1), (x2, y2), (0,255,0), 2)
                cv2.putText(output, f"{name} dist: {dist:.2}", (x1+5,y1-15), cv2.FONT_HERSHEY_COMPLEX, 1, box_col)

            else:
                bbox = det[0:4].astype(np.int32)
                x1, y1 = bbox[0], bbox[1]
                x2, y2 = bbox[0]+bbox[2], bbox[1]+bbox[3]

                cv2.rectangle(output, (x1, y1), (x2, y2), (0,0,255), 2)
                cv2.putText(output, f"dist: {dist:.2}", (x1+5,y1-15), cv2.FONT_HERSHEY_COMPLEX, 1, box_col)
                    
        # add time and fps counter
        curr_time = datetime().now()

        cv2.putText(output, f"{curr_time.strftime("%Y-%m-%d %H:%M:%S")}", (5,15), fontFace=1, fontScale=1, color=(0,255,0))
        cv2.putText(output, f"{fps} frames/sec", (5,30), fontFace=1, fontScale=1, color=(0,255,0))


        return output

    def loadKnownFaces(self, face_imgs_path: str) -> dict:
        
        # TODO
        # pull images from db and load to dir target_faces
        # calculate embeddings and save to output dictionary
        # add some face cropping and gamma correction

        self.KnownEmbs = dict()

        img = cv2.imread("target_faces/Josh0.jpg") # cropped image of a face
        name = "Josh"
        
        self.KnownEmbs[name] = self.frecogi_model.infer(img)

        print(f"{1} face(s) loaded...")
        return self.KnownEmbs
