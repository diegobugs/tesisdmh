import pandas as pd
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from util import DatabaseConnection as db

if __name__ == '__main__':
    database_connection = db.DatabaseConnection()
    rows = database_connection.query("SELECT * FROM lightning_data LIMIT 100")
    for row in rows:
        # print("data: {0}".format(row))
        start_time = row[3]
        end_time = row[4]
        type = row[5]
        latitude = row[6]
        longitude = row[7]
        peak_current = row[8]
        ic_height = row[9]
        number_of_sensors = row[10]
        ic_multiplicity = row[11]
        cg_multiplicity = row[12]
        geom = row[13]

        # print(latitude)

        """"
        1. Recorrer por tipo de descarga
        2. Recorrer mientras tiempo incio sea menor a tiempo final
        3. Sumar tiempo en lapso de 10 minutos
        4. recoger descargas dentro de coordenadas dadas, tipo de rayo y tiempo inicio y fin
        5. Sumar valor absoluto de peak_current
        6. detectar peak_current mayor a 1.000.000 de Amperios        
        """

polygon = Polygon([(-27.930452,-57.444440),(-25.596055,-56.774274),(-25.962093,-54.357282),(-29.204053,-55.324079),(-27.930452,-57.444440)])