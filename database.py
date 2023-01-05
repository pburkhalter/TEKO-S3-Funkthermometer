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
                CREATE TABLE IF NOT EXISTS data (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    timestamp DATE,
                    temperature INTEGER,
                    humidity INTEGER,
                    station TEXT
                );
            """)
        except sqlite.Error as er:
            raise DatabaseError("Something went wrong while setting up the database")

    def get(self, order="ROWID", sort="DESC", limit=1):
        try:
            self.__connection.execute("""
                SELECT * from data ORDER BY ? ? LIMIT ?
            """, (order, sort, limit))
        except sqlite.Error as er:
            raise DatabaseError("Something went wrong while reading from the database")

    def add(self, sid, timestamp, temperature, humidity, station):
        try:
            self.__connection.execute("""
                INSERT INTO data (id ,timestamp ,temperature ,humidity ,station)
                VALUES (?, ?, ?, ?, ?);
            """, (sid, timestamp, temperature, humidity, station))
        except sqlite.Error as er:
            raise DatabaseError("Something went wrong while adding data to the database")

    def remove(self, sid):
        pass

    def clean(self):
        pass

    def drop(self):
        pass

    def __iter__(self):
        pass
