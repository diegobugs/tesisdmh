
import pandas as pd
from util import DatabaseConnection as db
from util import PlotData as plt
from datetime import datetime
from datetime import timedelta
import numpy as np
import time
from sklearn.externals import joblib
# import pickle
from sklearn import svm
import os.path

if __name__ == '__main__':

    inicio_de_tiempo = time.time()
    print("Analisis iniciado: "+str(datetime.now()))

    database_connection = db.DatabaseConnection('190.128.205.75','rayos','cta','M9vNvgQ2=4os')

    diaAnalizarIni = datetime.strptime('2015-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    diaAnalizarFin = datetime.strptime('2015-12-30 00:00:00', '%Y-%m-%d %H:%M:%S')
    coordenadaAnalizar = '-57.606765,-25.284659'  # Asuncion2
    tiempoIntervalo = 10  # minutos
    diametroAnalizar = '40000'  # en metros

    tiempoAnalizarIni = diaAnalizarIni
    tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)


    print("Conectando a la base de datos...Descargas")
    rows = database_connection.query(
        "SELECT start_time,end_time,type,latitude,longitude,peak_current,ic_height,number_of_sensors,ic_multiplicity,cg_multiplicity,geom FROM lightning_data WHERE type=1 AND ST_DistanceSphere(geom, ST_MakePoint(" + coordenadaAnalizar + ")) <= " + diametroAnalizar + "  AND start_time >= to_timestamp('" + str(
            diaAnalizarIni) + "', 'YYYY-MM-DD HH24:MI:SS.MS') AND start_time <= to_timestamp('" + str(
            diaAnalizarFin) + "', 'YYYY-MM-DD HH24:MI:SS.MS')")
    print("Conectado")


    print("Preparando datos")
    df = pd.DataFrame(data=rows,columns=['start_time', 'end_time', 'type', 'latitude', 'longitude', 'peak_current', 'ic_height','number_of_sensors', 'ic_multiplicity', 'cg_multiplicity', 'geom'])

    rayosEnRango1M= []
    rayosEnRango5k=[]
    while tiempoAnalizarIni <= diaAnalizarFin:
        query = 'start_time >="' + datetime.strftime(tiempoAnalizarIni,'%Y-%m-%d %H:%M:%S') + '" and start_time<="' + datetime.strftime(tiempoAnalizarFin, '%Y-%m-%d %H:%M:%S') + '"'
        datosAnalisis = df.query(query)

        peak_current = 0  # Corriente pico INTENSIDAD
        qty = 0 # Cantidad de rayos DENSIDAD
        if not datosAnalisis.empty:
            # Bucle de cada rayo
            for i, row in enumerate(datosAnalisis.itertuples(),1):
                peak_current += abs(row.peak_current)
                qty+=1

                if (peak_current >= 900000 | peak_current <=1100000):
                    rayosEnRango1M.append(qty)

                if (peak_current >= 400000 | peak_current <= 600000):
                    rayosEnRango5k.append(qty)
                #endif
            #endfor de rayos
        # endif hay datos de descargas

        tiempoAnalizarIni = tiempoAnalizarFin
        tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)
    #endwhile recorrido de tiempo de analisis

    tiempo_final = time.time()
    tiempo_transcurrido = tiempo_final - inicio_de_tiempo
    print("Tiempo transcurrido de análisis: " + str(tiempo_transcurrido) + " segundos")

    suma1M = 0
    cuenta = 0
    for i in rayosEnRango1M:
        suma1M+=i
        cuenta +=1
        # print(i)
    promedio = 0
    if cuenta>0:
        promedio = suma1M/cuenta
    print("Promedio 1M:"+str(promedio))

    suma5k = 0
    cuenta = 0
    for i in rayosEnRango5k:
        suma5k += i
        cuenta += 1

    promedio = 0
    if cuenta > 0:
        promedio = suma5k / cuenta
    print("Promedio 5k:" + str(promedio))

    exit(0)