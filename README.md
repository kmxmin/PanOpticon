# PanOpticon (Proof of Concept)

PanOpticon is a facial detection and recognition system

## Setting up the virtual environment

First run the following to initalise the virtual environment.

```
python3 -m venv env
```

This creates a folder called `env/` in your current directory. In order to activate the virtual environment need to run the following script.

```
source env/bin/activate
```

Now you should have `(env)` at the start of each line in the terminal, indicating that you are using your virtual environment. Next  we need to install all the packages we need to run the scripts. For that you need to run the following that upgrades pip and installs the neccesary dependencies.

```
pip install --upgrade pip
pip install -r requirements.txt
```

This step might take a while to execute. Once that is all done you can run the application using. Furthermore, make sure you have postgress installed and running on your computer.

```
python3 src/main.py
```

If you would like to add a face to the 

## Python Scripts

A brief run down of each file in the src directory along with what they are meant to do.

* **main.py**: Accepts command line arguments, which are then used to instatiate the administrative window or camera window.
  * "a" - luanches the amdinistrative window
  * "h" - provides a list of available cameras, each identified by a number
  * 0 - instatiates a camera window for the first camera on the device. 1 can be used if there is more than one camera connected to the machine
  * No command line arguments instatiates a camera window for the first camera connected to the computer.
* **admin_window.py**: administrative side of the application where you can add faces to database and verify the person in fornt of the . You can also check the event log.
* **camera.py**: 'client' side of the application
* **database.py**: everything database related from creating and connecting to (existing) database and querying it to store and fetch faces.
* **image_tools.py**: used for gamma correcting of the captured images and cropping the face in captured images.
* **sface.py**: contains only the SFace class sourced from the [OpenCV Zoo github repository.](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface)
* **yunet.py**: contians only the YuNet class sourced from the [OpenCV Zoo githuh repository.](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet)

This project also makes use of pretrained versions of SFace and YuNet found in the model directory. Models were also sourced from the [OpenCV Zoo github repository](https://github.com/opencv/opencv_zoo/tree/main/models), which is great resource of open source computer vision models.
