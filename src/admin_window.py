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


class AdminWindow:

    def __init__(self, fd_model_path: str, fr_model_path: str) -> None:
        self.root = tki.Tk()
        self.root.title("PanOpticon Administrator")

        self.output_path = os.getcwd() + "/images"

        # load in detection and recognition models
        self.fdetect_model = YuNet(modelPath=fd_model_path, confThreshold=0.8)
        self.frecogi_model = SFace(modelPath=fr_model_path, disType=1)

        self.root.bind("<Escape>", self.on_close)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # create/connect to database
        self.myDB = database.Database(
            "postgres", "2518", "PanOpticon", "localhost"
        )  # change this line to your local server credentials
        # self.myDB.create_tables() # to reset database; comment this out if you don't want to reset it

        self.video_feed = cv2.VideoCapture(0)
        self.width = int(self.video_feed.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.video_feed.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fdetect_model.setInputSize([self.width, self.height])

        self.setup_UI()

        if not os.path.exists("images"):
            os.mkdir("images")

        self.camera_loop()
        self.root.mainloop()

    # adjust the brightness of the image if needed
    def brightness_check(frame: np) -> np:
        brightness = image_tools.brightness_check(frame)

        if brightness > 200:
            frame = image_tools.adjust_gamma(frame, 0.5)  # make the image darker

        elif brightness < 40:
            frame = image_tools.adjust_gamma(frame, 2.5)  # make the image brighter

        return frame

    # uses current time to name the captured photo
    def get_file_name(self) -> tuple:
        ts = datetime.datetime.now()  # ts for time stamp
        file_name = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
        path = os.path.sep.join((self.output_path, file_name))

        return path, file_name

    # display captured img
    def display_thumbnail(self, img: np, display_text: str) -> None:
        thumbnailWindow = tki.Toplevel()
        thumbnailWindow.title("Preview Image")

        img = img.resize((160, 160))
        thumbnail = ImageTk.PhotoImage(img)
        panel = tki.Label(thumbnailWindow, image=thumbnail)
        panel.image = thumbnail
        panel.pack()

        text_label = tki.Label(thumbnailWindow, text=display_text)
        text_label.pack()

    # captures the frame and saves the image to outputPath
    def on_add(self):
        path, file_name = self.get_file_name()

        # takes a photo and crop it to save it as a thumbnail
        _, frame = self.video_feed.read()
        if frame is not None:

            frame = self.brightness_check(frame)

            frame, _ = image_tools.extract_face(frame, self.fdetect_model)

            cv2.imwrite(path, frame)

        first_name = simpledialog.askstring("Input", "First name: ")
        last_name = simpledialog.askstring("Input", "Last name: ")

        # convert img to numpy for manipulation
        img = Image.open(path)
        numpy_img = np.asarray(img)

        encoding = self.frecogi_model.infer(numpy_img)
        new_face, faceID = self.myDB.add_faces(first_name, last_name, encoding)

        if new_face:
            self.myDB.add_thumbnail(faceID, file_name)  # adding thumbnail to database
            display_text = "Hi, {}".format(first_name)

        self.display_thumbnail(numpy_img, display_text)

    # verifies the face against the database
    def verification(self, img: np) -> bool:
        self.known_encodings = (
            self.myDB.fetch_encodings()
        )  # fetch all the encodings stored in database

        this_emb = self.frecogi_model.infer(img)

        is_recognised = False

        for faceID in self.known_encodings:

            trg_emb = self.known_encodings[faceID]

            dist, is_recognised = self.frecogi_model.dist(trg_emb, this_emb)

            if is_recognised:
                identity = self.myDB.verification(faceID)
                display_text = "Hi, {}".format(identity)

                # if dist < 0.7 then add to mean encoding
                if dist < 0.7:
                    self.myDB.update_mean_encoding(faceID, this_emb, identity)

                return is_recognised, display_text

            else:
                return False, ""

    def on_verify(self):
        path, file_name = self.get_file_name()

        # takes a photo and crops the face
        _, frame = self.video_feed.read()
        if frame is not None:
            frame, _ = image_tools.extract_face(frame, self.fdetect_model)

            cv2.imwrite(path, frame)

        # convert img to numpy
        img = Image.open(file_name)
        numpy_img = np.asarray(img)

        is_recognised, display_text = self.verification(numpy_img)

        if not is_recognised:  # face does not exist on database
            self.myDB.verification("stranger")
            display_text = "Hi, stranger"

        self.display_thumbnail(img, display_text)

    def on_logs(self):
        event_window = tki.Toplevel()
        event_window.title("Event logs")
        event_window.config(width=300, height=600)

        eventLogs = self.myDB.fetch_event_logs()

        # Create a frame to hold the Text and Scrollbar widgets
        frame = tki.Frame(event_window)
        frame.pack(fill="both", expand=True)

        # Create the Text widget
        event_text = tki.Text(frame, wrap="word")
        event_text.pack(side="left", fill="both", expand=True)
        event_text.insert(tki.END, eventLogs)

        # Create the Scrollbar widget
        scrollbar = tki.Scrollbar(frame, orient="vertical", command=event_text.yview)
        scrollbar.pack(side="right", fill="y")

        # Configure the Text widget to use the Scrollbar
        event_text.config(yscrollcommand=scrollbar.set)

    # closes admin window
    def on_close(self):
        self.myDB.close_conn()
        self.video_feed.release()
        self.root.quit()

    # placing UI elements
    def setup_UI(self):
        self.camera_feed = tki.Label(
            self.root, width=1280, height=720, padx=10, pady=10
        )
        self.camera_feed.pack()

        self.btns_frame = tki.Frame(self.root)

        self.btn_add = tki.Button(
            self.btns_frame,
            command=self.on_add,
            text="add",
            padx=10,
            pady=10,
            background="#ACFFCA",
        )
        self.btn_verify = tki.Button(
            self.btns_frame,
            command=self.on_verify,
            text="verify",
            padx=10,
            pady=10,
            background="#FFACAC",
        )
        self.btn_log = tki.Button(
            self.btns_frame,
            command=self.on_logs,
            text="logs",
            padx=10,
            pady=10,
            background="#FEFFAC",
        )

        self.btn_add.pack(side="left")
        self.btn_verify.pack(side="left")
        self.btn_log.pack(side="left")

        self.btns_frame.pack(side="bottom")

    def camera_loop(self):
        _, frame = self.video_feed.read()
        if not self.video_feed.isOpened():
            print("Error: could not open video feed.")

            return

        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # cnverts BGR to RGB
        img = cv2.resize(img, (1280, 720))
        img = Image.fromarray(img)  # converts array to image
        imgTk = ImageTk.PhotoImage(img)  # converts image to tk bitmap

        self.camera_frame = imgTk
        self.camera_feed.configure(image=imgTk, height=720, width=1280)

        self.camera_feed.after(10, self.camera_loop)
