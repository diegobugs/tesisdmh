import pandas as pd
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from util import DatabaseConnection as db
from util import PlotData as plot
from datetime import datetime
from datetime import timedelta

if __name__ == '__main__':

    plot = plot.Plot()
    # plot.drawIntoMap(-57.623154, -25.280073,1)
    # plot.drawIntoMap(-57.603154, -25.284073, 1)
    # plot.printMap()
    # exit(0)
    database_connection = db.DatabaseConnection()
    diaAnalizarIni = datetime.strptime('2016-11-27 00:00:00', '%Y-%m-%d %H:%M:%S')
    diaAnalizarFin = datetime.strptime('2016-11-27 23:59:59', '%Y-%m-%d %H:%M:%S')

    coordenadaAnalizar = '-57.606765,-25.284659'
    diametroAnalizar = '30000' #en metros

    tiempoIntervalo = 10 #minutos

    tiempoAnalizarIni = diaAnalizarIni
    tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)

    rows = database_connection.query(
        "SELECT start_time,end_time,type,latitude,longitude,peak_current,ic_height,number_of_sensors,ic_multiplicity,cg_multiplicity,geom FROM lightning_data WHERE type=0 AND ST_DistanceSphere(geom, ST_MakePoint(" + coordenadaAnalizar + ")) <= " + diametroAnalizar + "  AND start_time >= to_timestamp('" + str(diaAnalizarIni) + "', 'YYYY-MM-DD HH24:MI:SS.MS') AND start_time <= to_timestamp('" + str(diaAnalizarFin) + "', 'YYYY-MM-DD HH24:MI:SS.MS')")
    df = pd.DataFrame(data=rows, columns=['start_time','end_time','type','latitude','longitude','peak_current','ic_height','number_of_sensors','ic_multiplicity','cg_multiplicity','geom'])

    while tiempoAnalizarIni <= diaAnalizarFin:

        query = 'start_time >="'+datetime.strftime(tiempoAnalizarIni, '%Y-%m-%d %H:%M:%S')+'" and start_time<="'+datetime.strftime(tiempoAnalizarFin, '%Y-%m-%d %H:%M:%S')+'"'
        # query = 'start_time >="'+strd1+'" and start_time <= "'+strd2+'"'

        # query = 'start_time >="2016-12-19 13:00:00" and start_time <= "2016-12-19 23:50:00"'
        datosAnalisis = df.query(query)

        # df = df[(df['start_time']>='"'+datetime.strftime(tiempoAnalizarIni, '%Y-%m-%d %H:%M:%S.%f')+'"') & (df['start_time']<='"'+datetime.strftime(tiempoAnalizarFin, '%Y-%m-%d %H:%M:%S.%f')+'"')]
        peak_current = 0 #Corriente pico
        if not datosAnalisis.empty:
            for i, row in enumerate(datosAnalisis.itertuples(),1):
                peak_current += abs(row.peak_current)

                # print(row.latitude,row.longitude)

                # print(row.start_time, abs(row.peak_current))
                if(peak_current >= 1000000):
                    print("########")
                    print("Posible evento severo. Amperaje de:", peak_current)
                    plot.drawIntoMap(row.longitude, row.latitude, row.type)
                    # Convertir hora UTC a hora local UTC -3
                    horaEvento = row.start_time - timedelta(hours=3)
                    print(horaEvento)


        tiempoAnalizarIni = tiempoAnalizarFin
        tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)
    plot.printMap()
    exit(0)

    """"
    1. Recorrer por tipo de descarga
    2. Recorrer mientras tiempo incio sea menor a tiempo final
    3. Sumar tiempo en lapso de 10 minutos
    4. recoger descargas dentro de coordenadas dadas, tipo de rayo y tiempo inicio y fin
    5. Sumar valor absoluto de peak_current
    6. detectar peak_current mayor a 1.000.000 de Amperios        
    """