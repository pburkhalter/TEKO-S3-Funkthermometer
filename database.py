import psycopg2


class DatabaseError(Exception):
    pass


class DatabaseConnector:

    def __init__(self):
        self.__connection = None
        self.__cursor = None

    def connect(self, filepath=None):
        try:
            self.__connection = psycopg2.connect(
                host="localhost",
                database="measurement",
                user="measurement",
                password="measurement"
            )
        except psycopg2.errors as er:
            raise DatabaseError("Something went wrong while setting up the database")

        self.__connection.autocommit = True
        self.__cursor = self.__connection.cursor()

    def disconnect(self):
        self.__connection.commit()
        self.__connection.close()

    def setup(self):
        try:
            self.__cursor.execute("""
                CREATE TABLE IF NOT EXISTS measurement (
                    id SERIAL,
                    station TEXT,
                    timestamp TIMESTAMP,
                    temperature FLOAT,
                    humidity FLOAT
                );
            """)
        except psycopg2.errors as er:
            raise DatabaseError("Something went wrong while setting up the database")

    def get(self, limit=1):
        try:
            self.__cursor.execute("""
                SELECT *
                FROM measurement
                ORDER BY id DESC
                LIMIT %(limit)s
            """, {"limit": limit})
            records = self.__cursor.fetchall()
            return records
        except psycopg2.errors as er:
            raise DatabaseError("Something went wrong while reading from the database")

    def get_by_station(self, limit=1, station="T1"):
        try:
            self.__cursor.execute("""
                SELECT temperature, humidity, timestamp
                FROM measurement
                WHERE station = %(station)s
                ORDER BY id DESC
                LIMIT %(limit)s
            """, {"limit": limit,
                  "station": station})
            records = self.__cursor.fetchall()
            return records
        except psycopg2.errors as er:
            raise DatabaseError("Something went wrong while reading from the database")

    def add(self, station, timestamp, temperature, humidity):
        try:
            self.__cursor.execute("""
                INSERT INTO measurement (station ,timestamp ,temperature ,humidity)
                VALUES (%(station)s, %(timestamp)s, %(temperature)s, %(humidity)s);
            """, {"station": station,
                  "timestamp": timestamp,
                  "temperature": temperature,
                  "humidity": humidity})
        except psycopg2.errors as er:
            raise DatabaseError("Something went wrong while adding data to the database")

    def remove(self, sid):
        pass

    def clean(self):
        pass

    def drop(self):
        pass

    def __iter__(self):
        pass
