# handles camera input with realtime(ish) face detection and recognition

import cv2
import numpy as np

from datetime import datetime
from threading import Event

from database import vectorDB
from yunet import YuNet
from sface import SFace


class Camera():
    def __init__(self, fd_model_path: str, fr_model_path: str, camera=0) -> None:        

        # load in detection and recognition models
        self.fdetect_model = YuNet(modelPath=fd_model_path, confThreshold=0.8)
        self.frecogi_model = SFace(modelPath=fr_model_path, disType=1)
        print("models loaded...")

        self.myDB = vectorDB('postgres', '2518', 'FaceDetection', 'localhost')  # connect to DB
        self.loadKnownFaces()

        self.vid_stream = cv2.VideoCapture(camera)
        self.width = int(self.vid_stream.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.vid_stream.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.is_on = Event()
        self.is_on.clear()

        self.fdetect_model.setInputSize([self.width, self.height])

        self.tm = cv2.TickMeter()

    def camera_loop(self):
        
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

            frame = self.visualize(frame, fdetect_results, fps=self.tm.getFPS())

            cv2.imshow("camera", frame)

            self.tm.reset()
    
    def verify(self, img) -> tuple:
        name_tag = "?unknown?"

        this_emb = self.frecogi_model.infer(img)
        

        for name in self.KnownEmbs:
        
            trg_emb = self.KnownEmbs[name]
            dist, is_recognised = self.frecogi_model.dist(trg_emb, this_emb)

            if is_recognised:
                name_tag = self.myDB.fetchName(name)
        
        return name_tag, dist, is_recognised

    def visualize(self, img, results, fps=None) -> np.ndarray:
        # adds fps counter and time 
        # adds bounding boxes and name tags

        output = img.copy()

        for i, det in enumerate(results):
            
            bbox = det[0:4].astype(np.int32)
            x1, y1 = bbox[0], bbox[1]
            x2, y2 = bbox[0]+bbox[2], bbox[1]+bbox[3]

            face_img = img[y1:y2, x1:x2]
            face_img = cv2.resize(face_img, (160,160))

            name, dist, is_recognised = self.verify(face_img)

            if is_recognised:

                cv2.rectangle(output, (x1, y1), (x2, y2), (0,255,0), 2)
                cv2.putText(output, f"{name} dist: {dist:.2f}", (x1+5,y1-15), 1, 1, (0,255,0))

            else:

                cv2.rectangle(output, (x1, y1), (x2, y2), (0,0,255), 2)
                cv2.putText(output, f"{name} dist: {dist:.2f}", (x1+5,y1-15), 1, 1, (0,255,255))
                    
        # add time and fps counter
        curr_time = datetime.now()

        cv2.putText(output, f"{curr_time.strftime("%Y-%m-%d %H:%M:%S")}", (5,15), fontFace=1, fontScale=1, color=(0,255,0))
        cv2.putText(output, f"{fps:.2f} frames/sec", (5,30), fontFace=1, fontScale=1, color=(0,255,0))

        return output

    def loadKnownFaces(self) -> dict:

        self.KnownEmbs = dict()

        self.KnownEmbs = self.myDB.fetchEncodings()
        numOfFaces = self.myDB.numOfFaces()

        print("{} face(s) loaded...".format(numOfFaces))
        
        #print(self.KnownEmbs)

        return self.KnownEmbs

def get_avail_cameras() -> list:

    output = list()
    up_to = 10

    # check upto first 10 cameras
    for i in range(up_to):
        cap = cv2.VideoCapture(i)

        if cap.read()[0]:
            output.append(i)
            cap.release()
        else:
            break

    return output
