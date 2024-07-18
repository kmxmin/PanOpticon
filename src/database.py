# postgreSQL database to store faces & encodings & events


import psycopg2  # make sure to install postgreSQL on your machine

# also make sure your postgreSQL server is running if running locally
from psycopg2 import sql
import pickle
import numpy as np


class vectorDB:  # can be improved using actual vector DB

    # connects to db
    def __init__(
        self, user: str, password: str, database: str, host="localhost"
    ):  # if host not given, uses localhost
        self.user = user
        self.password = password
        self.database = database
        self.host = host

        self.conn = psycopg2.connect(
            user=self.user, password=self.password, host=self.host
        )

        print("Connection established :)")

        self.conn.set_session(autocommit=True)

        cursor = self.conn.cursor()

        cursor.execute(
            sql.SQL("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s"),
            [database],
        )  # checks if db with this name exists; if not create new

        exists = cursor.fetchone()

        if not exists:
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database))
            )  # ensures no duplicate DB is created
            print("Database: {} successfully created!".format(database))
        else:
            print("Successfully connected to database: {}!".format(database))

    # used to initialise tables; otherwise could be used to reset the DB
    # tableName is set to 'Faces'
    def createTables(self):
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
        )  # thumbnail is stored as binary data; could be changed to storing image path rather for bigger model

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
        )

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

        print("Successfully created tables: Faces & Encoding & Events!")

        cursor.close()

    # add thumbnail img to row in Faces - called when registering new Face
    def addThumbnail(self, id: str, imgPath: str):
        cursor = self.conn.cursor()

        cursor.execute("UPDATE Faces SET thumbnail = %s WHERE ID = %s", (imgPath, id))

        print("Successfully added thumbnail!")

        cursor.close()

    # calculate the mean encoding
    def updateMeanEncoding(self, id: str, encoding: np, firstName: str):
        cursor = self.conn.cursor()

        fetch_query = "SELECT encoding, timesAdded FROM Encoding WHERE id = %s"
        cursor.execute(fetch_query, (id,))
        meanEncoding, timesAdded = cursor.fetchone()

        unpickledMeanEncoding = pickle.loads(
            meanEncoding
        )  # back to numpy for calculation
        unpickledMeanEncoding = unpickledMeanEncoding * timesAdded
        unpickledMeanEncoding = (
            np.add(unpickledMeanEncoding, encoding) / timesAdded
        )  # this gets the mean encoding

        pickledEncoding = pickle.dumps(
            unpickledMeanEncoding
        )  # dumps() serialises an object

        updateEncodingQuery = "UPDATE Encoding SET encoding = %s, timesAdded = timesAdded + 1 WHERE id = %s"
        cursor.execute(updateEncodingQuery, (pickledEncoding, id))

        logEvent = "INSERT INTO Events (ID, description) VALUES (%s, %s)"
        description = "Old face {} was used to update Faces table.".format(firstName)
        eventQuery = (id, description)
        cursor.execute(logEvent, eventQuery)

        cursor.close()

    # adds/updates encoding to/of Faces table
    def addFaces(
        self, firstName: str, lastName: str, encoding: np
    ) -> tuple:  # returns isNewFace : bool and id : str
        cursor = self.conn.cursor()

        # id is created uniquely using 5 letters of full name & 3 digit number (000); e.g. Min Kim would be KmMin001
        id = lastName[0] + lastName[-1]
        if len(firstName) < 3:
            id += firstName + "X"
        else:
            id += firstName[0] + firstName[1] + firstName[2]

        cursor.execute("SELECT COUNT(*) FROM Faces WHERE ID LIKE %s", (id + "%",))
        count = cursor.fetchone()[0]

        # if there are people with same id, check if it's the same person
        # for now, we assume if their full names match, it's the same person. but this needs to be changed - could be improved
        if count > 0:
            cursor.execute(
                "SELECT ID FROM Faces WHERE ID LIKE %s AND firstName = %s AND lastName = %s",
                (id + "%", firstName, lastName),
            )
            matchingRows = cursor.fetchall()

            if matchingRows:
                print("There is already a person with the same id and full name.")

                # don't add them to Faces table; only update the encoding
                for row in matchingRows:
                    id = row[0]
                    # print("Old face {}'s ID: {}".format(firstName, id))

                self.updateMeanEncoding(id, encoding, firstName)

                print("Successfully added {}'s encoding to db!".format(firstName))

                cursor.close()

                return False, ""

            # there are people with same ID, but with different names
            else:

                addFace = (
                    "INSERT INTO Faces (ID, firstName, lastName) VALUES (%s, %s, %s)"
                )

                count += count
                if (
                    count < 10
                ):  # this block assumes that there won't be more than 999 people with same id
                    id += "00" + str(count)
                elif count < 100:
                    id += "0" + str(count)
                else:
                    id += str(count)
                print("New face {}'s new ID is: ".format(firstName) + id)

                cursor.execute(addFace, (id, firstName, lastName))
                print("Successfully added {} with ID: {} to db!".format(firstName, id))

                # now add pickledEncoding
                pickledEncoding = pickle.dumps(encoding)  # dumps() serialises an object

                addEncoding = "INSERT INTO Encoding (ID, encoding, timesAdded) VALUES (%s, %s, 1)"  # new face thus first time being added; timesAdded = 1
                encodingQuery = (id, pickledEncoding)
                cursor.execute(addEncoding, encodingQuery)

                logEvent = "INSERT INTO Events (ID, description) VALUES (%s, %s)"
                description = "New face {} added to Encoding table.".format(firstName)
                eventQuery = (id, description)
                cursor.execute(logEvent, eventQuery)

                print("Successfully added {}'s encoding to db!".format(firstName))

                cursor.close()

                return True, id  # then add thumbnail

        else:
            # new Face! - proceed to add their face to Faces table
            addFace = "INSERT INTO Faces (ID, firstName, lastName) VALUES (%s, %s, %s)"

            count = 1  # 001 is the first person with that id
            if (
                count < 10
            ):  # this block assumes that there won't be more than 999 people with same id
                id += "00" + str(count)
            elif count < 100:
                id += "0" + str(count)
            else:
                id += str(count)
            print("New face {}'s new ID is: ".format(firstName) + id)

            cursor.execute(addFace, (id, firstName, lastName))
            print("Successfully added {} with ID: {} to db!".format(firstName, id))

            # now add pickledEncoding
            pickledEncoding = pickle.dumps(encoding)  # dumps() serialises an object

            addEncoding = "INSERT INTO Encoding (ID, encoding, timesAdded) VALUES (%s, %s, 1)"  # new face thus first time being added; timesAdded = 1
            encodingQuery = (id, pickledEncoding)
            cursor.execute(addEncoding, encodingQuery)

            logEvent = "INSERT INTO Events (ID, description) VALUES (%s, %s)"
            description = "New face {} added to Encoding table.".format(firstName)
            eventQuery = (id, description)
            cursor.execute(logEvent, eventQuery)

            print("Successfully added {}'s encoding to db!".format(firstName))

            cursor.close()

            return True, id  # then add thumbnail

    # prints/returns the number of registered faces
    def numOfFaces(self):
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Faces")
        count = cursor.fetchone()[0]

        print("There are {} faces on Faces table.".format(count))

        cursor.close()

        return count

    # returns dictionary of encodings for all the registered faces {id:encoding}
    def fetchEncodings(self):
        cursor = self.conn.cursor()

        try:
            cursor.execute("SELECT ID, encoding FROM Encoding")

            # Fetch all results
            results = cursor.fetchall()

            result = {}
            for row in results:
                id, encoding = row
                unpickledEncoding = pickle.loads(encoding)  # back to numpy
                result[id] = unpickledEncoding

            return result

        except psycopg2.Error as e:
            print("Error executing query:", e)
            self.conn.rollback()

        cursor.close()

    # returns dictionary of encodings for specified person {id:encoding}
    def fetchEncodingOf(self, identity: str):
        cursor = self.conn.cursor()

        fullName = identity.split()
        firstName = fullName[0]
        lastName = fullName[1]

        cursor.execute(
            "SELECT ID FROM Faces WHERE firstName=%s AND lastName=%s",
            (firstName, lastName),
        )
        results = cursor.fetchone()
        try:
            if results:
                # if person exists on db, get their id
                id = results[0]
                print("{} found with id: {}".format(firstName, id))

                query = "SELECT encoding FROM Encoding WHERE ID='{}'".format(id)
                cursor.execute(query)

                encoding = cursor.fetchone()[0]
                unpickledEncoding = pickle.loads(encoding)  # back to numpy

                result = {}
                result[id] = unpickledEncoding

                return result

        except psycopg2.Error as e:
            print("Error executing query:", e)
            self.conn.rollback()

        cursor.close()

    # adds verification log onto Events table; verification happens in admin_window.onVerify()
    def verification(self, id) -> str:
        cursor = self.conn.cursor()
        logEvent = "INSERT INTO Events (ID, description) VALUES (%s, %s)"

        if id == "stranger":
            description = "Unregistered face tried to verify on the system."
            eventQuery = "INSERT INTO Events (description) VALUES (%s)"
            cursor.execute(eventQuery, (description,))

            cursor.close()

            return id

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

        result = ""

        if not eventLogs:
            cursor.close()
            return "The system is new! No event was logged."

        else:
            for row in eventLogs:
                for tup in row:
                    result += str(tup) + " "
                result += "\n"

            cursor.close()
            return result

    def close_conn(self):
        self.conn.close()
        print("Successfully disconnected from db!")
