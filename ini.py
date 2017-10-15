import pandas as pd
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from util import DatabaseConnection as db

if __name__ == '__main__':
    database_connection = db.DatabaseConnection()
    rows = database_connection.query("SELECT * FROM lightning_data LIMIT 100")
    for row in rows:
        print("data: {0}".format(row))

polygon = Polygon([(-27.930452,-57.444440),(-25.596055,-56.774274),(-25.962093,-54.357282),(-29.204053,-55.324079),(-27.930452,-57.444440)])