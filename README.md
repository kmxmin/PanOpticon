# PanOpticon (prototype)

Hey MIn, heres some instructions to get up and running with the python scripts I wrote.

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

* **Peekaboo.py**: is the actual application with the gui and all. This is what the final product/project is as an executable.
* **cropper.py:**  is a cropping tool that made using mtcnn
* **scratch.py**: is just a scratch file. Ignore it
* **facenet.py:** is a package that does the facial recognition/verification
* **camerastream_client.py**: is just camera tool that
