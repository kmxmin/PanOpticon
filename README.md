# PanOpticon (prototype)

## Setting up the virtual environment

First run the following to initalise the virtual environment.

```
python3 -m venv env
```

This creates a folder called `env/` in your current directory. In order to activate the virtual environment need to run the following script.

```
source env/bin/activate
```

Now you should have `(env)` at the start of each line in the terminal. The virtual environment is like a blank install of the python interpreter. So we need to install all the packages we need to run the scripts. For that you need to run the following

```
pip install -r requirements.txt
```

That step should take a while since some of the packages are quite beefy. Also try and copy the facenet model in the current directory

Once that is all done you can run the application using

```
python3 src/Peekaboo.py
```

## Python Scripts and what they (should) do

* **main.py**: is the actual application with the gui and all. This is what the final product/project is as an executable.
* **admin_window.py**: administrative side of the application where you can add faces to database and verify who the person is. You can also check the event log.
* **camera.py**: 'client' side of the application 
* **database.py**: everything database related from creating and connecting to (existing) database and querying it to store and fetch faces.
* **image_tools.py**: used for gamma correcting of the captured images and cropping the face in captured images.
* **sface.py**:
* **yunet.py**:
