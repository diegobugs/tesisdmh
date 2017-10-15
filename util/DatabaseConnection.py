import psycopg2
from pprint import pprint
import time

class DatabaseConnection:
    def __init__(self):
        try:
            self.connection = psycopg2.connect(
                "dbname='rayos' user='cta' host='rayos' password='M9vNvgQ2=4os' port='5432'")
            self.cursor = self.connection.cursor()
        except (RuntimeError, TypeError, NameError):
            pprint("No se puede conectar a la base de datos" + NameError)

    def query(self, query):
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        return rows