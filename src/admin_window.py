import tkinter as tki
from tkinter import simpledialog
from PIL import Image, ImageTk
import cv2
import os
import datetime
from database import *

from yunet import YuNet
from sface import SFace

class admin_window():
    
    def __init__(self, fd_model_path: str, fr_model_path: str ):
        
        self.root = tki.Tk()
        self.outputPath = "C:/Users/rlaal/Desktop/ByteOrbit/faceDetect/images"  # where the captured images are saved
        
        self.root.bind("<Escape>", self.onClose)
        self.root.protocol("WM_DELETE_WINDOW", self.onClose)
        self.root.title("Peekaboo Administrator")
        self.root.geometry("1000x500") # Peekaboo window size

        self.fdetect_model = YuNet(fd_model_path)
        self.frecogi_model = SFace(fr_model_path)
        print("models loaded")

        self.myDB = vectorDB('postgres', '2518', 'FaceDetection', 'localhost')

        self.setupUI()

        self.video_feed = cv2.VideoCapture(0)
        self.fdetect_model.setInputSize([self.video_feed.get(cv2.CAP_PROP_FRAME_WIDTH), 
                                         self.video_feed.get(cv2.CAP_PROP_FRAME_HEIGHT)])

        self.cameraLoop()
        self.root.mainloop()

        
    # captures the frame and saves the image to outputPath
    def onAdd(self):
        ts = datetime.datetime.now() # ts for time stamp
        fileName = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
        p = os.path.sep.join((self.outputPath, fileName))

        _, frame = self.video_feed.read()
        if frame is not None:

            brightness = brightness_check(frame)

            if brightness > 200:   
                frame = adjust_gamma(frame, 0.5)
                print("Making it darker")
            elif brightness < 60:
                frame = adjust_gamma(frame, 1.5)
                print("Making it brighter")
            else:
                pass    # lighting is good

            frame = cropper.extract_face(frame)

            cv2.imwrite(p, frame)
            print("Frame captured")

            fileName = self.outputPath + "/" +  fileName
            #print("Saved img: " + fileName)

        
        # could use the name+timestamp to name captured photo
        firstName = simpledialog.askstring("Input", "First name: ")
        lastName = simpledialog.askstring("Input", "Last name: ")
        
        # convert img to numpy to store on DB
        img = Image.open(fileName)
        numpyImg = asarray(img)

        # add to DB
        newFace, id = self.myDB.addFaces(firstName, lastName, img_to_encoding(numpyImg, self.FRmodel))
        if newFace:
            self.myDB.addThumbnail(id, fileName)


        # display captured img
        thumbnailWindow = tki.Toplevel()
        thumbnailWindow.title("Preview Image")
        thumbnailWindow.geometry("300x300")

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
            
            
            frame = cropper.extract_face(frame)

            cv2.imwrite(p, frame)
            print("Frame captured")

            fileName = self.outputPath + "/" +  fileName
            #print("Saved img: " + fileName)
            
        #firstName = simpledialog.askstring("Input", "First name: ")    # this was for using verifyID() instead of verify()
        #lastName = simpledialog.askstring("Input", "Last name: ")
        #fullName = firstName + ' ' + lastName

        # convert img to numpy
        img = Image.open(fileName)
        numpyImg = asarray(img)

        verification, identity = self.myDB.verify(numpyImg, self.FRmodel)

        if verification:
            displayText = "Hi, {}".format(identity)
        else:
            displayText = "Unknown face"

        # display captured img
        thumbnailWindow = tki.Toplevel()
        thumbnailWindow.title("Preview Image")
        thumbnailWindow.geometry("300x300")

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


    def setupUI(self):
        # placing UI elements

        self.camera_feed = tki.Label(self.root, width=1280, height=720, padx=10, pady=10)
        self.camera_feed.pack()

        self.btns_frame = tki.Frame(self.root)
        self.btns_frame.grid

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
        img = cv2.resize(img, (650, 650))
        img = Image.fromarray(img) # converts array to image
        imgTk = ImageTk.PhotoImage(img) # converts image to tk bitmap

        self.camera_frame = imgTk
        self.camera_feed.configure(image=imgTk, height=360, width=640)

        self.camera_feed.after(10, self.cameraLoop) 
