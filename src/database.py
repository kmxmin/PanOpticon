# postgreSQL database to store faces (name & img_encoding) & events


import psycopg2 # make sure to install postgreSQL on your machine
                # also make sure your postgreSQL server is running if running locally
from psycopg2 import sql
#from pgvector.psycopg2 import register_vector   # pip install pgvector
import pickle 
import numpy as np 
import tensorflow as tf



class vectorDB:     # can be improved using actual vector DB

    # connects to db
    # myDB = vectorDB('postgres', '2518', 'FaceDetect', 'localhost')
    def __init__(self, user : str, password : str, database : str, host = 'localhost'): # if host not given, uses localhost
        self.user = user
        self.password = password    # probably not the safest approach to get pw ??
        self.database = database
        self.host = host

        self.conn = psycopg2.connect(user=self.user, password=self.password, host=self.host)
        
        print("Connection established :)")

        self.conn.set_session(autocommit=True)
    
        cursor = self.conn.cursor()

        cursor.execute(sql.SQL("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s"), [database]) # checks if db with this name exists

        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))  # ensures no duplicate DB is created
            print("Database: {} successfully created!".format(database))
        else:
            print("Successfully connected to database: {}!".format(database))

        # cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        # CREATE EXTENSION IF NOT EXISTS vector ## still need to work on this
        # register_vector(self.conn) 
        

    
    # myDB.createFaceTable()
    # tableName is set to 'Faces'
    def createFaceTable(self):

        cursor = self.conn.cursor()

        # might be good idea to make it optional to delete existing Faces table
        cursor.execute("DROP TABLE IF EXISTS Faces CASCADE")    # deletes table if exists
        cursor.execute("DROP TABLE IF EXISTS Encoding")
        cursor.execute("DROP TABLE IF EXISTS Events")
        

        # id uuid PRIMARY KEY DEFAULT uuid_generate_v4() // if SERIAL PRIMARY KEY not sufficient; CREATE EXTENSION in that case
        cursor.execute( # table to store ID and name
            """
            CREATE TABLE IF NOT EXISTS Faces(
            ID VARCHAR(8) PRIMARY KEY,
            firstName VARCHAR(255) NOT NULL,
            lastName VARCHAR(255) NOT NULL,
            thumbnail BYTEA
            )
            """
        )   # thumbnail is stored as binary data; could be changed to storing image path rather for bigger model

        cursor.execute( # table to store encoding for each face; can have multiple encodings per ID (face)
            """
            CREATE TABLE Encoding(
            ID VARCHAR(8) REFERENCES Faces,
            encoding BYTEA NOT NULL,
            timestamp TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )

        cursor.execute( # table to store events
            """
            CREATE TABLE Events(
            eventID SERIAL PRIMARY KEY,
            ID VARCHAR(8) REFERENCES Faces,
            description VARCHAR(255),
            timestamp TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )

        print("Successfully created tables: Faces & Encoding & Events!")

        cursor.close()


    # add thumbnail img to row in Faces - called when registering new Face
    def addThumbnail(self, id : str, imgPath : str):

        cursor = self.conn.cursor()
        
        cursor.execute("UPDATE Faces SET thumbnail = %s WHERE ID = %s", (imgPath, id))

        print("Successfully added thumbnail!")

        cursor.close()


    # myDB.addFaces('andrew', 'tate', img_to_encoding('images/andrew.jpg', FRmodel))
    def addFaces(self, firstName : str, lastName : str, encoding : np) -> tuple:  # returns newFace : bool and id : str
    
        cursor = self.conn.cursor()

        # id is created uniquely using 5 letters of full name & 3 digit number (000)
        id = lastName[0] + lastName[-1]
        if len(firstName) < 3:
            id += firstName + 'X'
        else:
            id += firstName[0] + firstName[1] + firstName[2]

        cursor.execute("SELECT COUNT(*) FROM Faces WHERE ID LIKE %s", (id + '%',))
        count = cursor.fetchone()[0]
        #print(f"Number of rows where name starts with '{id}': {count}")

        # if there are people with same id, check if it's same person
        # for now, we assume if their full names match, it's the same person. but this needs to be changed
        if count > 0:
            cursor.execute("SELECT ID FROM Faces WHERE ID LIKE %s AND firstName = %s AND lastName = %s", 
                           (id + '%', firstName, lastName))
            matchingRows = cursor.fetchall()

            if matchingRows:
                print("There is already a person with the same id and full name.")
                # don't add them to Faces table; only add the encoding
                for row in matchingRows:
                    id = row[0]
                    #print("Old face {}'s ID: {}".format(firstName, id))

            # now add pickledEncoding
            pickledEncoding = pickle.dumps(encoding) # dumps() serialises an object

            addEncoding = ("INSERT INTO Encoding (ID, encoding) VALUES (%s, %s)")
            encodingQuery = (id, pickledEncoding)
            cursor.execute(addEncoding, encodingQuery)

            logEvent = ("INSERT INTO Events (ID, description) VALUES (%s, %s)")
            description = "Old face of {} added to Faces table.".format(firstName)
            eventQuery = (id, description)
            cursor.execute(logEvent, eventQuery)

            print("Successfully added {}'s encoding to db!".format(firstName))

            cursor.close()
            
            return False, ''
                
        else:
            # new Face! - proceed to add their face to Faces table
            addFace = ("INSERT INTO Faces (ID, firstName, lastName) VALUES (%s, %s, %s)")

            count += 1  # 001 is the first person with that id
            if count < 10:      # this block assumes that there won't be more than 999 people with same id
                id += "00" + str(count)
            elif count < 100:
                id += "0" + str(count)
            else:
                id += str(count)
            print("New face {}'s new ID is: ".format(firstName) + id)

            # add thumbnail

            cursor.execute(addFace, (id, firstName, lastName))
            print("Successfully added {} with ID: {} to db!".format(firstName, id))

            # now add pickledEncoding
            pickledEncoding = pickle.dumps(encoding) # dumps() serialises an object

            addEncoding = ("INSERT INTO Encoding (ID, encoding) VALUES (%s, %s)")
            encodingQuery = (id, pickledEncoding)
            cursor.execute(addEncoding, encodingQuery)

            logEvent = ("INSERT INTO Events (ID, description) VALUES (%s, %s)")
            description = "New face {} added to Encoding table.".format(firstName)
            eventQuery = (id, description)
            cursor.execute(logEvent, eventQuery)

            print("Successfully added {}'s encoding to db!".format(firstName))

            cursor.close()

            return True, id # then add thumbnail
        

    '''
    # if identity exists on db, it verifies. Otherwise says it doesn't exist.
    def verifyID(self, img: np.ndarray, identity : str, model):
        fullName = identity.split()
        firstName = fullName[0]
        lastName = fullName[1]

        cursor = self.conn.cursor()
        
        encoding = img_to_encoding(img, model)

        # we are still assuming people with same full names are one person
        cursor.execute("SELECT ID FROM Faces WHERE firstName=%s AND lastName=%s", (firstName, lastName))
        result = cursor.fetchone()

        try:
            if result:
                # if person exists on db, get their id
                id = result[0]
                #print("{} found with ID: {}".format(firstName, id))

                query = ("SELECT encoding FROM Encoding WHERE ID='{}'".format(id))
                cursor.execute(query)
        
                unpickledEncoding = pickle.loads(cursor.fetchone()[0])     # back to numpy

                dist = np.linalg.norm(tf.subtract(unpickledEncoding, encoding))
                
                if dist < 0.7:
                    print(f"It's " + str(identity) + ", welcome in! dist " + str(dist))
                    door_open = True

                    # add (face) to Events
                    logEvent = ("INSERT INTO Events (ID, description) VALUES (%s, %s)")
                    description = "{} was verified on the system.".format(firstName)
                    eventQuery = (id, description)
                    cursor.execute(logEvent, eventQuery)

                else:
                    print("It's not " + str(identity) + ", please go away. dist:"+ str(dist))
                    door_open = False

                    # add (UNKNOWN) to Events
                    description = "Someone tried to verifiy impostering {}".format(firstName)
                    cursor.execute(("INSERT INTO Events (description) VALUES %s"), (description))

                return dist, door_open
            
            else:
                description = "Unregistered face tried to verify on the system."
                cursor.execute(("INSERT INTO Events (description) VALUES %s"), (description))
                print("{} not found on db :( Add the face first before verification.".format(identity))
       
        except psycopg2.Error as e:
            print("Error executing query:", e)
            self.conn.rollback()

        cursor.close()
    '''
    

    # prints/returns the number of registered faces
    def numOfFaces(self):
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Faces")
        count = cursor.fetchone()[0]

        print("There are {} faces on Faces table.".format(count))

        cursor.close()

        return count



    # returns dictionary of encodings for all the registered faces
    # encodings are the most recently added one for each face
    def fetchEncodings(self):
        cursor = self.conn.cursor()

        try:
            # Execute the CTE query to get the most recent encoding for each ID
            cursor.execute(
                """
                WITH RankedEncodings AS (
                    SELECT 
                        ID, 
                        encoding, 
                        ROW_NUMBER() OVER (PARTITION BY ID ORDER BY timestamp DESC) AS rn
                    FROM Encoding
                )
                SELECT ID, encoding
                FROM RankedEncodings
                WHERE rn = 1;
                """
            )
            
            # Fetch all results
            results = cursor.fetchall()
            
            result = {}
            for row in results:
                id, encoding = row
                unpickledEncoding = pickle.loads(encoding)     # back to numpy
                result[id] = unpickledEncoding

            return result

        except psycopg2.Error as e:
            print("Error executing query:", e)
            self.conn.rollback()

        cursor.close()

    
    # returns dictionary of encodings for specified person
    def fetchEncodingOf(self, identity : str):
        cursor = self.conn.cursor()

        fullName = identity.split()
        firstName = fullName[0]
        lastName = fullName[1]

        cursor.execute("SELECT ID FROM Faces WHERE firstName=%s AND lastName=%s", (firstName, lastName))
        results = cursor.fetchone()
        try:
            if results:
                # if person exists on db, get their id
                id = results[0]
                print("{} found with id: {}".format(firstName, id))

                query = ("SELECT encoding FROM Encoding WHERE ID='{}'".format(id))
                cursor.execute(query)

                encoding = cursor.fetchone()[0]
                unpickledEncoding = pickle.loads(encoding)     # back to numpy

                result = {}
                result[id] = unpickledEncoding

                return result

        except psycopg2.Error as e:
            print("Error executing query:", e)
            self.conn.rollback()

        cursor.close()


    # take image and finds their identity on DB
    # returns true if exists
    def verify(self, capturedEncoding : np.ndarray, model) -> tuple:
        cursor = self.conn.cursor()

        #capturedEncoding = img_to_encoding(image, model)

        min_dist = 100

        allEncodings = self.fetchEncodings() # this returns dictionary {ID: encoding}
        
        for encoding in allEncodings.values():
            dist = np.linalg.norm(tf.subtract(encoding, capturedEncoding))

            if dist < min_dist:
                min_dist = dist
                lastEncoding = encoding

        if min_dist > 0.7:
            #print("Not in the database.")
            cursor.close()
            return False, ""
        
        else:
            for id, encoding in allEncodings.items():
                if np.array_equal(encoding, lastEncoding):
                    cursor.execute("SELECT (firstName) FROM Faces WHERE ID = '{}'".format(id))
                    identity = cursor.fetchone()[0]

            #print ("Hi " + str(identity) + ", the distance is " + str(min_dist))
            
            cursor.close()
            return True, str(identity)
        
    
    # adds verification log onto Events table
    def verification(self, id):
        cursor = self.conn.cursor()
        logEvent = ("INSERT INTO Events (ID, description) VALUES (%s, %s)")

        if id == "stranger":
            description = "Unregistered face tried to verify on the system."
            eventQuery = "INSERT INTO Events (description) VALUES {}".format(description)
            cursor.execute(eventQuery)

            cursor.close()

            return "stranger"
        else:
            cursor.execute("SELECT (firstName) FROM Faces WHERE ID = '{}'".format(id))
            firstName = cursor.fetchone()[0]
            
            description = "{} was verified on the system.".format(firstName)
            
            eventQuery = (id, description)
            cursor.execute(logEvent, eventQuery)

            cursor.close()

            return firstName



    def fetchEventLogs(self) -> str:
        cursor = self.conn.cursor()

        cursor.execute("SELECT (description, timestamp) FROM Events")
        eventLogs = cursor.fetchall()

        result = ''

        if not eventLogs:
            cursor.close()
            return "The system is new! No event was logged."
        
        else:
            for row in eventLogs:
                for tup in row:
                    result += str(tup) + ' '
                result += '\n'
            
            cursor.close()
            return result
        
    
        
    # myDB.close_conn()
    def close_conn(self):
        self.conn.close()
        print("Successfully disconnected from db!")


