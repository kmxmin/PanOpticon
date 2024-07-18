# postgreSQL database to store faces & encodings & events


import psycopg2 # make sure to install postgreSQL on your machine
                # also make sure your postgreSQL server is running if running locally
from psycopg2 import sql
import pickle 
import numpy as np 



class Database: 

    # connects to database
    def __init__(self, user : str, password : str, database : str, host = 'localhost'):
        self.user = user
        self.password = password 
        self.database = database
        self.host = host

        self.conn = psycopg2.connect(user=self.user, password=self.password, host=self.host)
        self.conn.set_session(autocommit=True)
    
        cursor = self.conn.cursor()

        # checks if this database exists; if not create new
        cursor.execute(sql.SQL("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s"), [database]) 

        exists = cursor.fetchone()
        
        if not exists:
            # ensures no duplicate database is created
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))  

    

    # used to initialise tables; otherwise could be used to reset the DB
    def create_tables(self):
        cursor = self.conn.cursor()

        # deletes table if exists
        cursor.execute("DROP TABLE IF EXISTS Faces CASCADE")    
        cursor.execute("DROP TABLE IF EXISTS Encoding")
        cursor.execute("DROP TABLE IF EXISTS Events")
        
        cursor.execute( 
            """
            CREATE TABLE IF NOT EXISTS Faces(
            ID VARCHAR(8) PRIMARY KEY,
            firstName VARCHAR(255) NOT NULL,
            lastName VARCHAR(255) NOT NULL,
            thumbnail BYTEA
            )
            """
        )   # thumbnail is stored as binary data; could be changed to storing image path rather for bigger model

        # stored encoding is a mean encoding which gets calculated everytime you add a new face for each person
        cursor.execute(
            """
            CREATE TABLE Encoding(
            ID VARCHAR(8) REFERENCES Faces,
            encoding BYTEA NOT NULL,
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            timesAdded INT
            )
            """
        )   # timesAdded to keep track of how many times the encoding of a person were updated

        cursor.execute(
            """
            CREATE TABLE Events(
            eventID SERIAL PRIMARY KEY,
            ID VARCHAR(8) REFERENCES Faces,
            description VARCHAR(255),
            timestamp TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )

        cursor.close()



    # add thumbnail img to row in Faces - called when registering new Face
    def add_thumbnail(self, faceID : str, imgPath : str):
        cursor = self.conn.cursor()
        
        cursor.execute("UPDATE Faces SET thumbnail = %s WHERE ID = %s", (imgPath, faceID))

        print("Successfully added thumbnail!")

        cursor.close()



    # calculate the mean encoding and update Encoding table
    def update_mean_encoding(self, faceID : str, encoding : np, first_name : str):
        cursor = self.conn.cursor()

        fetch_query = "SELECT encoding, timesAdded FROM Encoding WHERE id = %s"
        cursor.execute(fetch_query, (faceID,))
        mean_encoding, timesAdded = cursor.fetchone()

        unpickled_mean_encoding = pickle.loads(mean_encoding)     # back to numpy for calculation
        unpickled_mean_encoding = unpickled_mean_encoding * timesAdded
        unpickled_mean_encoding = np.add(unpickled_mean_encoding, encoding) / timesAdded    # this gets the mean encoding

        pickled_encoding = pickle.dumps(unpickled_mean_encoding) # dumps() serialises an object

        update_encoding_query = ("UPDATE Encoding SET encoding = %s, timesAdded = timesAdded + 1 WHERE id = %s")
        cursor.execute(update_encoding_query, (pickled_encoding, faceID))

        logEvent = ("INSERT INTO Events (ID, description) VALUES (%s, %s)")
        description = "Old face {} was used to update Faces table.".format(first_name)
        event_query = (faceID, description)
        cursor.execute(logEvent, event_query)

        cursor.close()



    # id is created uniquely using 5 letters of full name & 3 digits number (000); e.g. Min Kim would be KmMin001
    def assign_face_ID(self, first_name : str, last_name : str) -> str:
        
        faceID = last_name[0] + last_name[-1]
        if len(first_name) < 3:
            faceID += first_name + 'X'
        else:
            faceID += first_name[0] + first_name[1] + first_name[2]

        return faceID



    # add new face to Faces table & update the mean encoding in Encoding table
    def add_new_face(self, faceID : str, first_name : str, last_name : str, encoding : np, count=1) -> None:
        cursor = self.conn.cursor()

        addFace = ("INSERT INTO Faces (ID, firstName, lastName) VALUES (%s, %s, %s)")

        # count represents the number proceeding the faceID
        if count < 10:      # we assume that there won't be more than 999 people with same id
            faceID += "00" + str(count)
        elif count < 100:
            faceID += "0" + str(count)
        else:
            faceID += str(count)

        cursor.execute(addFace, (faceID, first_name, last_name))

        pickled_encoding = pickle.dumps(encoding) # dumps() serialises an object

        add_encoding = ("INSERT INTO Encoding (ID, encoding, timesAdded) VALUES (%s, %s, 1)")    # new face thus first time being added; timesAdded = 1
        encoding_query = (faceID, pickled_encoding)
        cursor.execute(add_encoding, encoding_query)

        log_event = ("INSERT INTO Events (ID, description) VALUES (%s, %s)")
        description = "New face {} added to Encoding table.".format(first_name)
        event_query = (faceID, description)
        cursor.execute(log_event, event_query)

        cursor.close()



    # adds/updates encoding to/of Faces table
    def add_faces(self, first_name : str, last_name : str, encoding : np) -> tuple:  # returns is_new_face : bool and id : str
        cursor = self.conn.cursor()

        faceID = self.assign_face_ID(first_name, last_name)

        cursor.execute("SELECT COUNT(*) FROM Faces WHERE ID LIKE %s", (faceID + '%',))
        count = cursor.fetchone()[0]


        # if there are people with same id, check if it's the same person
        # for now, we assume if their full names match, it's the same person
        if count > 0:
            cursor.execute("SELECT ID FROM Faces WHERE ID LIKE %s AND firstName = %s AND lastName = %s", 
                           (faceID + '%', first_name, last_name))
            matching_rows = cursor.fetchall()

            if matching_rows:
                # if it is registered face, just update the mean encoding
                for row in matching_rows:
                    faceID = row[0]

                self.update_mean_encoding(faceID, encoding, first_name)

                cursor.close()

                return False, ''
            else:
                # there are people with same ID, but with different names
                self.add_new_face(faceID, first_name, last_name, encoding, (count+1))

                cursor.close()

                return True, faceID # then add thumbnail
        else:
            # there is no one with same ID
            self.add_new_face(faceID, first_name, last_name, encoding)

            cursor.close()

            return True, faceID
        
    

    # prints/returns the number of registered faces
    def num_of_faces(self) -> int:
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Faces")
        count = cursor.fetchone()[0]

        cursor.close()

        return count



    # returns dictionary of encodings for all the registered faces {id:encoding}
    def fetch_encodings(self) -> tuple:
        cursor = self.conn.cursor()

        try:
            cursor.execute("SELECT ID, encoding FROM Encoding")
   
            results = cursor.fetchall()
            
            result = {}
            for row in results:
                faceID, encoding = row
                unpickled_encoding = pickle.loads(encoding)     # back to numpy
                result[faceID] = unpickled_encoding

            return result

        except psycopg2.Error as e:
            self.conn.rollback()

        cursor.close()


    
    # returns dictionary of encodings for specified person {id:encoding}
    def fetch_encoding_of(self, identity : str) -> tuple:
        cursor = self.conn.cursor()

        full_name = identity.split()
        first_name = full_name[0]
        last_name = full_name[1]

        cursor.execute("SELECT ID FROM Faces WHERE firstName=%s AND lastName=%s", (first_name, last_name))
        results = cursor.fetchone()
        try:
            if results:
                # if person exists on db, get their id
                faceID = results[0]
                print("{} found with id: {}".format(first_name, faceID))

                query = ("SELECT encoding FROM Encoding WHERE ID='{}'".format(faceID))
                cursor.execute(query)

                encoding = cursor.fetchone()[0]
                unpickled_encoding = pickle.loads(encoding)     # back to numpy

                result = {}
                result[faceID] = unpickled_encoding

                return result

        except psycopg2.Error as e:
            self.conn.rollback()

        cursor.close()

        
    
    # adds verification log onto Events table; verification happens in admin_window.onVerify()
    def verification(self, faceID) -> str:
        cursor = self.conn.cursor()
        log_event = ("INSERT INTO Events (ID, description) VALUES (%s, %s)")

        if faceID == "stranger":
            description = "Unregistered face tried to verify on the system."
            event_query = "INSERT INTO Events (description) VALUES (%s)"
            cursor.execute(event_query, (description,))

            cursor.close()

            return faceID
        
        else:
            cursor.execute("SELECT (firstName) FROM Faces WHERE ID = '{}'".format(id))
            first_name = cursor.fetchone()[0]
            
            description = "{} was verified on the system.".format(first_name)
            event_query = (faceID, description)
            cursor.execute(log_event, event_query)

            cursor.close()

            return first_name



    def fetch_event_logs(self) -> str:
        cursor = self.conn.cursor()

        cursor.execute("SELECT (description, timestamp) FROM Events")
        event_logs = cursor.fetchall()

        result = ''

        if not event_logs:
            cursor.close()
            return "The system is new! No event was logged."
        
        else:
            for row in event_logs:
                for tup in row:
                    result += str(tup) + ' '
                result += '\n'
            
            cursor.close()
            return result
        


    def fetch_name(self, faceID : str):
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT (firstName) FROM Faces WHERE id = '{}'".format(faceID))
        first_name = cursor.fetchone()[0]

        cursor.close()

        return first_name
        

        
    def close_conn(self):
        self.conn.close()
        print("Successfully disconnected from db!")


