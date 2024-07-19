# PanOpticon (Proof of Concept)

PanOpticon is a facial detection and recognition system.

## Dependencies

python 3.8+
numpy==2.0.0
opencv-python==4.10.0.84
pillow==10.4.0
psycopg2-binary==2.9.9


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

This step might take a while to execute. 

## Setting up PostgreSQL
- PostgreSQL server
macOS: https://postgresapp.com/
Ubuntu: apt-get install postgresql
Windowns: https://www.postgresql.org/download/windows/

Furthermore, make sure you have PostgreSQL installed and the server is running on your computer. Use the username and the password you used on PostgreSQL admin to connect to the server. Change the below lines in camera.py and admin_window.py to use your credentials.

```
self.myDB = database.vectorDB(username, password, 'PanOpticon', 'localhost')     # change this line to your local server credentials
```

This would create/connect to the database (PanOpticon in the case above, but you can change the name of the database). When you create the database OR you want to reset the database, you must uncomment the below line in admin_window.py. Make sure you comment it out after the first bootup so that you don't reset the database.

```
self.myDB.createTables() # to reset DB;
```

Once that is all done you can run the application.

```
python3 src/main.py
```

## Python Scripts

A brief run down of each file in the src directory along with what they are meant to do.

* **main.py**: Accepts command line arguments, which are then used to instatiate the administrative window or camera window.
  * "a" - luanches the amdinistrative window
  * "h" - provides a list of available cameras, each identified by a number
  * 0 - instatiates a camera window for the first camera on the device. 1 can be used if there is more than one camera connected to the machine
  * No command line arguments instatiates a camera window for the first camera connected to the computer.
* **admin_window.py**: administrative side of the application where you can add faces to database and verify the person in fornt of the camera. You can also check the event log.
* **camera.py**: 'client' side of the application.
* **database.py**: everything database related from creating and connecting to (existing) database and querying it to store and fetch faces.
* **image_tools.py**: used for gamma correcting of the captured images and cropping the face in captured images.
* **sface.py**: contains only the SFace class sourced from the [OpenCV Zoo github repository.](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface)
* **yunet.py**: contians only the YuNet class sourced from the [OpenCV Zoo githuh repository.](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet)

This project also makes use of pretrained versions of SFace and YuNet found in the model directory. Models were also sourced from the [OpenCV Zoo github repository](https://github.com/opencv/opencv_zoo/tree/main/models), which is great resource of open source computer vision models.
