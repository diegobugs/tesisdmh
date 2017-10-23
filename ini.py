import pandas as pd
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from util import DatabaseConnection as db
from datetime import datetime
from datetime import timedelta

if __name__ == '__main__':
    database_connection = db.DatabaseConnection()
    diaAnalizarIni = datetime.strptime('2016-12-19 13:00:00.0000', '%Y-%m-%d %H:%M:%S.%f')
    diaAnalizarFin = datetime.strptime('2016-12-19 13:59:59.0000', '%Y-%m-%d %H:%M:%S.%f')

    coordenadaAnalizar = '-57.692849,-25.212378'
    diametroAnalizar = '10000' #en metros

    tiempoIntervalo = 10 #minutos

    tiempoAnalizarIni = diaAnalizarIni
    tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)

    rows = database_connection.query(
        "SELECT start_time,end_time,type,latitude,longitude,peak_current,ic_height,number_of_sensors,ic_multiplicity,cg_multiplicity,geom FROM lightning_data WHERE ST_DistanceSphere(geom, ST_MakePoint(" + coordenadaAnalizar + ")) <= " + diametroAnalizar + "  AND start_time >= to_timestamp('" + str(diaAnalizarIni) + "', 'YYYY-MM-DD HH24:MI:SS.MS') AND start_time <= to_timestamp('" + str(diaAnalizarFin) + "', 'YYYY-MM-DD HH24:MI:SS.MS') LIMIT 500")
    df = pd.DataFrame(data=rows, columns=['start_time','end_time','type','latitude','longitude','peak_current','ic_height','number_of_sensors','ic_multiplicity','cg_multiplicity','geom'])

    while tiempoAnalizarIni <= diaAnalizarFin:
        strd1 = datetime.strftime(tiempoAnalizarIni, '%Y-%m-%d %H:%M:%S.%f')
        strd2 = datetime.strftime(tiempoAnalizarFin, '%Y-%m-%d %H:%M:%S.%f')


        # query = 'start_time >="'+datetime.strftime(tiempoAnalizarIni, '%Y-%m-%d %H:%M:%S.%f')+'" and start_time<="'+datetime.strftime(tiempoAnalizarFin, '%Y-%m-%d %H:%M:%S.%f')+'"'
        query = 'start_time >="'+strd1+'" and start_time <= "'+strd2+'"'
        df = df.query(query)
        print(df)
        exit(0)
        # df = df[(df['start_time']>='"'+datetime.strftime(tiempoAnalizarIni, '%Y-%m-%d %H:%M:%S.%f')+'"') & (df['start_time']<='"'+datetime.strftime(tiempoAnalizarFin, '%Y-%m-%d %H:%M:%S.%f')+'"')]

        if not df.empty:
            for d in df: #df tiene todos los registros de descargas entre los tiempos dados en lapso de tiempoIntervalo minutos
                print(d)


        tiempoAnalizarIni = tiempoAnalizarFin
        tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)

    exit(0)


    rows = database_connection.query("SELECT start_time,end_time,type,latitude,longitude,peak_current,ic_height,number_of_sensors,ic_multiplicity,cg_multiplicity,geom FROM lightning_data WHERE ST_DistanceSphere(geom, ST_MakePoint("+coordenadaAnalizar+")) <= "+diametroAnalizar+"  AND start_time >= to_timestamp('2017-01-01 00:00:00', 'YYYY-MM-DD HH24:MI:SS.MS') AND start_time <= to_timestamp('2017-01-20 00:10:00', 'YYYY-MM-DD HH24:MI:SS.MS') LIMIT 1000")
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