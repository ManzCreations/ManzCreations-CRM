import os

import pymysql


class DBConnector:
    def __init__(self):
        self.host = os.environ.get('DB_HOST', 'localhost')
        self.user = os.environ.get('DB_USER', 'root')
        self.password = os.environ.get('DB_PASS', 'Easton21!')
        self.dbname = os.environ.get('DB_NAME', 'Empty_CRM')
        self.connection = None

    def connect(self):
        """Establish a connection to the database."""
        if self.connection is None:
            try:
                self.connection = pymysql.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    db=self.dbname,
                    cursorclass=pymysql.cursors.DictCursor
                )
            except pymysql.MySQLError as e:
                print(f"ERROR: Cannot connect to database: {e}")
                raise e

    def execute_query(self, query, params=None):
        """Execute a given SQL query with optional parameters."""
        self.connect()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                return cursor.fetchall()
        except pymysql.MySQLError as e:
            self.connection.rollback()
            print(f"ERROR: Cannot execute query: {e}")
            raise e

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
