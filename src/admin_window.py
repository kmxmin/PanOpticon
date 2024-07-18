import tkinter as tki
from tkinter import simpledialog
from PIL import Image, ImageTk
import cv2
import os
import datetime

import database
import image_tools
import numpy as np

from yunet import YuNet
from sface import SFace


class admin_window():
    
    def __init__(self, fd_model_path: str, fr_model_path: str) -> None:
        self.root = tki.Tk()
        self.outputPath = "C:/Users/rlaal/Desktop/ByteOrbit/PanOpticon/images"  # where the captured images are saved - change according to your local machine
        print("outputpath: " + self.outputPath)

        # load in detection and recognition models
        self.fdetect_model = YuNet(modelPath=fd_model_path, confThreshold=0.8)
        self.frecogi_model = SFace(modelPath=fr_model_path, disType=1)
        print("models loaded...")
        
        self.root.bind("<Escape>", self.onClose)
        self.root.protocol("WM_DELETE_WINDOW", self.onClose)
        self.root.title("PanOpticon Administrator")
        # self.root.geometry("1000x500") # Admin window size

        self.myDB = database.vectorDB('postgres', '2518', 'PanOpticon', 'localhost')     # change this line to your local server credentials
        #self.myDB.createTables() # to reset DB; comment this out if you don't want to reset it

        self.video_feed = cv2.VideoCapture(0)
        self.width = int(self.video_feed.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.video_feed.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fdetect_model.setInputSize([self.width, self.height])

        self.setupUI()

        if not os.path.exists("images"):
            os.mkdir("images")

        self.cameraLoop()
        self.root.mainloop()


        
    # captures the frame and saves the image to outputPath
    def onAdd(self):
        ts = datetime.datetime.now() # ts for time stamp
        fileName = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
        p = os.path.sep.join((self.outputPath, fileName))

        _, frame = self.video_feed.read()
        if frame is not None:

            brightness = image_tools.brightness_check(frame)

            if brightness > 200:   
                frame = image_tools.adjust_gamma(frame, 0.5)
                print("Making it darker")
            elif brightness < 40:
                frame = image_tools.adjust_gamma(frame, 2.5)
                print("Making it brighter")
            else:
                print("Lighting is good")
                pass    

            frame, _ = image_tools.extract_face(frame, self.fdetect_model)

            cv2.imwrite(p, frame)
            print("Frame captured")

            fileName = self.outputPath + "/" +  fileName

        
        firstName = simpledialog.askstring("Input", "First name: ")
        lastName = simpledialog.askstring("Input", "Last name: ")

        # convert img to numpy
        img = Image.open(fileName)
        numpyImg = np.asarray(img)

        encoding = self.frecogi_model.infer(numpyImg)
        newFace, id = self.myDB.addFaces(firstName, lastName, encoding)

        if newFace:
            self.myDB.addThumbnail(id, fileName)    # adding thumbnail to DB

        # display captured img
        thumbnailWindow = tki.Toplevel()
        thumbnailWindow.title("Preview Image")

        img = img.resize((160,160))
        thumbnail = ImageTk.PhotoImage(img)
        panel = tki.Label(thumbnailWindow, image = thumbnail)
        panel.image = thumbnail
        panel.pack()

        fullName = "Hi, " + firstName + ' ' + lastName
        text_label = tki.Label(thumbnailWindow, text=fullName)
        text_label.pack()


    
    def onVerify(self):
        ts = datetime.datetime.now() # ts for time stamp
        fileName = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
        p = os.path.sep.join((self.outputPath, fileName))

        _, frame = self.video_feed.read()
        if frame is not None:
            frame, _ = image_tools.extract_face(frame, self.fdetect_model)

            cv2.imwrite(p, frame)
            print("Frame captured")

            fileName = self.outputPath + "/" +  fileName

        # convert img to numpy
        img = Image.open(fileName)
        numpyImg = np.asarray(img)

        self.KnownEmbs = self.myDB.fetchEncodings()

        this_emb = self.frecogi_model.infer(numpyImg)

        is_recognised = False

        for id in self.KnownEmbs:
        
            trg_emb = self.KnownEmbs[id]

            dist, is_recognised = self.frecogi_model.dist(trg_emb, this_emb)

            if is_recognised:
                identity = self.myDB.verification(id)
                displayText = "Hi, {}".format(identity)

                # if dist < 0.7 then add to mean encoding
                if dist < 0.7:
                    self.myDB.updateMeanEncoding(id, this_emb, identity)

                break
            else:
                continue
        
        if not is_recognised:
            identity = self.myDB.verification("stranger")
            displayText = "Hi, stranger"


        # display captured img
        thumbnailWindow = tki.Toplevel()
        thumbnailWindow.title("Preview Image")

        img = img.resize((160,160))
        thumbnail = ImageTk.PhotoImage(img)
        panel = tki.Label(thumbnailWindow, image = thumbnail)
        panel.image = thumbnail
        panel.pack()

        text_label = tki.Label(thumbnailWindow, text = displayText)
        text_label.pack()



    def onLogs(self):
        eventWindow = tki.Toplevel()
        eventWindow.title("Event logs")
        eventWindow.config(width=300, height=600)

        eventLogs = self.myDB.fetchEventLogs()

        # Create a frame to hold the Text and Scrollbar widgets
        frame = tki.Frame(eventWindow)
        frame.pack(fill="both", expand=True)

        # Create the Text widget
        eventText = tki.Text(frame, wrap="word")
        eventText.pack(side="left", fill="both", expand=True)
        eventText.insert(tki.END, eventLogs)

        # Create the Scrollbar widget
        scrollbar = tki.Scrollbar(frame, orient="vertical", command=eventText.yview)
        scrollbar.pack(side="right", fill="y")

        # Configure the Text widget to use the Scrollbar
        eventText.config(yscrollcommand=scrollbar.set)



    def onClose(self):
        self.myDB.close_conn()
        self.video_feed.release()
        self.root.quit()



    # placing UI elements
    def setupUI(self):
        self.camera_feed = tki.Label(self.root, width=1280, height=720, padx=10, pady=10)
        self.camera_feed.pack()

        self.btns_frame = tki.Frame(self.root)
        # self.btns_frame.grid

        self.btn_add = tki.Button(self.btns_frame, command=self.onAdd, text="add", padx=10, pady=10, background='#ACFFCA')
        self.btn_verify = tki.Button(self.btns_frame, command=self.onVerify, text="verify", padx=10, pady=10, background='#FFACAC')
        self.btn_log = tki.Button(self.btns_frame, command=self.onLogs, text="logs", padx=10, pady=10, background='#FEFFAC')
        
        self.btn_add.pack(side="left")
        self.btn_verify.pack(side="left")
        self.btn_log.pack(side="left")

        self.btns_frame.pack(side="bottom")



    def cameraLoop(self):
        _, frame = self.video_feed.read()
        if not self.video_feed.isOpened():
            print("Error: could not open video feed.")

            return
            
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # cnverts BGR to RGB
        img = cv2.resize(img, (1280, 720))
        img = Image.fromarray(img) # converts array to image
        imgTk = ImageTk.PhotoImage(img) # converts image to tk bitmap

        self.camera_frame = imgTk
        self.camera_feed.configure(image=imgTk, height=720, width=1280)

        self.camera_feed.after(10, self.cameraLoop) 



