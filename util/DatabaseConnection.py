import psycopg2
from pprint import pprint
import time

class DatabaseConnection:
    def __init__(self, host, dbname, user,password):
        try:
            self.connection = psycopg2.connect(
                "dbname='"+dbname+"' user='"+user+"' host='"+host+"' password='"+password+"' port='5432'")
            self.cursor = self.connection.cursor()
        except (RuntimeError, TypeError, NameError):
            pprint("No se puede conectar a la base de datos" + NameError)

    def query(self, query):
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        return rows