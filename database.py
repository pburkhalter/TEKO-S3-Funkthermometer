import sqlite3 as sqlite


class DatabaseError(Exception):
    pass


class DatabaseConnector:

    def __init__(self, filepath='test.db'):
        self.__connection = None
        self.__filepath = filepath

    def connect(self, filepath=None):
        filepath = filepath or self.__filepath

        if not self.__connection:
            self.__connection = sqlite.connect(filepath)

    def disconnect(self):
        self.__connection.commit()
        self.__connection.close()
        self.__connection = None

    def setup(self):
        try:
            self.__connection.execute("""
                CREATE TABLE DATA (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    timestamp DATE,
                    temperature INTEGER,
                    humidity INTEGER,
                    station TEXT,
                );
            """)
        except DatabaseError:
            raise DatabaseError("Something went wrong while setting up the database")
        except ConnectionError:
            raise DatabaseError("Database connection not yet initiated")

    def add(self, timestamp, temperature, humidity, station):
        pass

    def remove(self, id):
        pass

    def get(self, id):
        pass

    def filter(self, statement):
        pass

    def __iter__(self):
        pass
