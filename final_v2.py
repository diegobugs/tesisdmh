
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

    diaAnalizarIni = datetime.strptime('2015-05-03 00:00:00', '%Y-%m-%d %H:%M:%S')
    diaAnalizarFin = datetime.strptime('2015-05-04 00:00:00', '%Y-%m-%d %H:%M:%S')
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


    database_connection = db.DatabaseConnection('localhost', 'precip', 'postgres', '12345')

    print("Conectando a la base de datos...Precipitaciones")

    estaciones = "86218,86217,86214,86206,86207,86208"

    rows = database_connection.query(
        "SELECT codigo_estacion,nombre_estacion,latitud,longitud,fecha_observacion,valor_registrado,valor_corregido FROM precipitacion WHERE codigo_estacion IN ("+estaciones+") AND fecha_observacion >= to_timestamp('" + str(
            diaAnalizarIni) + "', 'YYYY-MM-DD HH24:MI:SS.MS') AND fecha_observacion <= to_timestamp('" + str(
            diaAnalizarFin) + "', 'YYYY-MM-DD HH24:MI:SS.MS')")
    print("Conectado")

    print("Preparando datos")
    dfP = pd.DataFrame(data=rows,
                       columns=['codigo_estacion', 'nombre_estacion', 'latitud', 'longitud', 'fecha_observacion',
                                'valor_registrado', 'valor_corregido'])
    print("Inicio de bucle")


    y = [0,10]
    X = [[0,0],[150,1000000]]

    # Definir el aprendizaje

    clf = svm.SVC(kernel='rbf', C=1.0, cache_size=500)
    # clf = SVC(kernel='rbf', C=1.0)
    # saveModel = False
    if os.path.exists('modelo.sav'):
        clf = joblib.load('modelo.sav')
        # result = loaded_model.score(X_test, Y_test)

    while tiempoAnalizarIni <= diaAnalizarFin:
        query = 'start_time >="' + datetime.strftime(tiempoAnalizarIni,'%Y-%m-%d %H:%M:%S') + '" and start_time<="' + datetime.strftime(tiempoAnalizarFin, '%Y-%m-%d %H:%M:%S') + '"'
        datosAnalisis = df.query(query)

        peak_current = 0  # Corriente pico INTENSIDAD
        HoraFinalCelula = None
        HoraInicialCelula = None
        EvoPuntoInicial = []
        EvoPuntoFinal = []
        printPosibleWeather = False
        qty = 0 # Cantidad de rayos DENSIDAD
        if not datosAnalisis.empty:

            # Bucle de cada rayo
            for i, row in enumerate(datosAnalisis.itertuples(),1):
                peak_current += abs(row.peak_current)
                qty+=1

                if (peak_current >= 1000000):

                    # Se alcanzó los 1.000.000 de amperios

                    printPosibleWeather = True

                    # Si supera los 1.000.000 de pico de corriente
                    # Generar poligono de los ultimos 45 minutos
                    tiempoTormentaIni = tiempoAnalizarIni + timedelta(minutes=45)

                    # rs = database_connection.query(
                    #     "SELECT start_time,end_time,type,latitude,longitude,peak_current,ic_height,number_of_sensors,ic_multiplicity,cg_multiplicity,geom FROM lightning_data WHERE type=1 AND ST_DistanceSphere(geom, ST_MakePoint(" + coordenadaAnalizar + ")) <= " + "80000" + "  AND start_time >= to_timestamp('" + str(
                    #         diaAnalizarIni) + "', 'YYYY-MM-DD HH24:MI:SS.MS') AND start_time <= to_timestamp('" + str(
                    #         diaAnalizarFin) + "', 'YYYY-MM-DD HH24:MI:SS.MS')")
                    # dff = pd.DataFrame(data=rs, columns=['start_time', 'end_time', 'type', 'latitude', 'longitude',
                    #                                      'peak_current', 'ic_height', 'number_of_sensors',
                    #                                      'ic_multiplicity', 'cg_multiplicity', 'geom'])

                    if HoraFinalCelula is None:
                        HoraFinalCelula = row.start_time
                    #endif
                #endif
            #endfor de rayos
        # endif hay datos de descargas


        # Consulta de precipitaciones
        query = 'fecha_observacion >="' + datetime.strftime(tiempoAnalizarIni + timedelta(minutes=50),'%Y-%m-%d %H:%M:%S') + '" and fecha_observacion < "' + datetime.strftime(tiempoAnalizarIni + timedelta(minutes=90), '%Y-%m-%d %H:%M:%S') + '"'
        datosAnalisis = dfP.query(query)
        precipitacion = 0
        qtyE = 0 #Cantidad de estaciones usadas
        if not datosAnalisis.empty:
            # Bucle de cada precipitacion
            for i, row in enumerate(datosAnalisis.itertuples(),1):
                qtyE += 1
                if precipitacion < row.valor_registrado:
                    precipitacion = row.valor_registrado



                # print(str(row.nombre_estacion)+" "+str(row.fecha_observacion)+" "+str(row.valor_registrado))


        # Mostrar en pantalla Hora analizada, intensidad y densidad de descargas electricas
        # if printPosibleWeather:
        #     print("Hora " + str(tiempoAnalizarIni) + " Intensidad:" + str(peak_current) + " Densidad:" + str(qty)+" Precipitacion:"+str(precipitacion)+" Estaciones:"+str(qtyE))
        # endif


        # x.append(precipitacion)
        # y.append(peak_current)

        X.append([qty,peak_current])

        a = 10 if precipitacion>10 else 0

        y.append(a)


        # Generar aprendizaje, agregar conocimiento al clf (Clasificador)
        # if not os.path.exists('modelo.sav'):
            # clf = joblib.load('modelo.sav')
        # clf.fit(X, y)
        # saveModel = True



        Z = [qty, peak_current]
        Z = np.reshape(Z, (1, -1))

        # Obtener una prediccion de tormenta del clasificador
        prediccion = clf.predict(Z)

        print("Hora " + str(tiempoAnalizarIni) + " Intensidad:" + str(peak_current) + " Densidad:" + str(
            qty) + " Precipitacion:" + str(precipitacion) + " Predicción:" + ("Tormenta" if prediccion==10 else "Nada"))




        tiempoAnalizarIni = tiempoAnalizarFin
        tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)
    #endwhile recorrido de tiempo de analisis

    tiempo_final = time.time()
    tiempo_transcurrido = tiempo_final - inicio_de_tiempo
    print("Tiempo transcurrido de análisis: " + str(tiempo_transcurrido) + " segundos")
    # if saveModel == True:
    #     joblib.dump(clf, 'modelo.sav')

    exit(0)