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
import csv

# Configuraciones por defecto
writeAnalisis = False
saveModel = False

if __name__ == '__main__':

    # Definicion por defecto de los .csv de conocimiento
    y = [0, 5, 10]
    X = [[0, 0], [40, 500000], [80, 1000000]]
    if not os.path.exists('dataset\clf_data.csv'):
        pd.DataFrame(data=X).to_csv('dataset\clf_data.csv', sep=";", mode='w', index=False, header=False)
    if not os.path.exists('dataset\clf_know.csv'):
        pd.DataFrame(data=y).to_csv('dataset\clf_know.csv', sep=";", mode='w', index=False, header=False)
    X, y = [], []
    with open('dataset\clf_data.csv', 'rt') as clf_data:
        spamreader = csv.reader(clf_data, delimiter=';')
        for row in spamreader:
            X.append([int(row[0]), int(row[1])])
    with open('dataset\clf_know.csv', 'rt') as clf_know:
        spamreader = csv.reader(clf_know, delimiter=';')
        for row in spamreader:
            y.append(int(row[0]))

    # Establecer un tiempo de inicio del calculo para saber cuanto demora
    inicio_de_tiempo = time.time()
    print("Analisis iniciado: " + str(datetime.now()))

    # Conexion a la base de datos de descargas electricas
    database_connection = db.DatabaseConnection('190.128.205.75', 'rayos', 'cta', 'M9vNvgQ2=4os')

    # Parametros para buscar descargas
    diaAnalizarIni = datetime.strptime('2015-05-03 06:00:00', '%Y-%m-%d %H:%M:%S')
    diaAnalizarFin = datetime.strptime('2015-05-03 10:00:00', '%Y-%m-%d %H:%M:%S')
    coordenadaAnalizar = '-57.606765,-25.284659'  # Asuncion2
    tiempoIntervalo = 10  # minutos
    diametroAnalizar = '40000'  # en metros

    # Definicion de tiempos a ser analizados, estas variables iran iterando en un bucle segun el tiempoIntervalo
    tiempoAnalizarIni = diaAnalizarIni
    tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)

    print("Conectando a la base de datos...Descargas")
    rows = database_connection.query(
        "SELECT start_time,end_time,type,latitude,longitude,peak_current,ic_height,number_of_sensors,ic_multiplicity,cg_multiplicity,geom FROM lightning_data WHERE type=1 AND ST_DistanceSphere(geom, ST_MakePoint(" + coordenadaAnalizar + ")) <= " + diametroAnalizar + "  AND start_time >= to_timestamp('" + str(
            diaAnalizarIni) + "', 'YYYY-MM-DD HH24:MI:SS.MS') AND start_time <= to_timestamp('" + str(
            diaAnalizarFin) + "', 'YYYY-MM-DD HH24:MI:SS.MS')")
    print("Conectado")

    print("Preparando datos")
    df = pd.DataFrame(data=rows,
                      columns=['start_time', 'end_time', 'type', 'latitude', 'longitude', 'peak_current', 'ic_height',
                               'number_of_sensors', 'ic_multiplicity', 'cg_multiplicity', 'geom'])

    # Conexion con base de datos de precipitaciones
    database_connection = db.DatabaseConnection('localhost', 'precip', 'postgres', '12345')
    print("Conectando a la base de datos...Precipitaciones")
    estaciones = "86218,86217,86214,86206,86207,86208"
    rows = database_connection.query(
        "SELECT codigo_estacion,nombre_estacion,latitud,longitud,fecha_observacion,valor_registrado,valor_corregido FROM precipitacion WHERE codigo_estacion IN (" + estaciones + ") AND fecha_observacion >= to_timestamp('" + str(
            diaAnalizarIni) + "', 'YYYY-MM-DD HH24:MI:SS.MS') AND fecha_observacion <= to_timestamp('" + str(
            diaAnalizarFin) + "', 'YYYY-MM-DD HH24:MI:SS.MS')")
    print("Conectado")

    print("Preparando datos")
    dfP = pd.DataFrame(data=rows,
                       columns=['codigo_estacion', 'nombre_estacion', 'latitud', 'longitud', 'fecha_observacion',
                                'valor_registrado', 'valor_corregido'])
    print("Inicio de bucle")

    # Definir el aprendizaje

    if saveModel == True:
        # Inicializar el clasificador
        clf = svm.SVC(kernel='rbf', C=1.0, cache_size=500)
    else:
        # Verificar que exista el modelo
        if os.path.exists('modelo.sav'):
            clf = joblib.load('modelo.sav')
        else:
            print("ALERTA: No existe el modelo. Se generará un nuevo modelo.")
            saveModel = True
            clf = svm.SVC(kernel='rbf', C=1.0, cache_size=500)

    analisis_data = []
    while tiempoAnalizarIni <= diaAnalizarFin:
        query = 'start_time >="' + datetime.strftime(tiempoAnalizarIni,
                                                     '%Y-%m-%d %H:%M:%S') + '" and start_time<="' + datetime.strftime(
            tiempoAnalizarFin, '%Y-%m-%d %H:%M:%S') + '"'
        datosAnalisis = df.query(query)

        peak_current = 0  # Corriente pico INTENSIDAD
        qty = 0  # Cantidad de rayos DENSIDAD

        # Si el dataset de descargas no se encuentra vacío
        if not datosAnalisis.empty:
            # Bucle de cada rayo

            # Obtener INTENSIDAD Y DENSIDAD
            for i, row in enumerate(datosAnalisis.itertuples(), 1):
                peak_current += abs(row.peak_current)
                qty += 1
                # endfor
        # endif hay datos de descargas

        # Consulta de precipitaciones
        # Las precipitaciones obtenidas entre 50 y 90 minutos luego del tiempo de descrgas eléctricas
        query = 'fecha_observacion >="' + datetime.strftime(tiempoAnalizarIni + timedelta(minutes=50),
                                                            '%Y-%m-%d %H:%M:%S') + '" and fecha_observacion < "' + datetime.strftime(
            tiempoAnalizarIni + timedelta(minutes=90), '%Y-%m-%d %H:%M:%S') + '"'
        datosAnalisis = dfP.query(query)

        # Definición de variables para contar cantidad de estaciones utilizadas
        qtyE = 0  # Cantidad de estaciones usadas
        if not datosAnalisis.empty:
            # Bucle de cada precipitacion
            for i, row in enumerate(datosAnalisis.itertuples(), 1):
                qtyE += 1
                # Se obtiene la mayor cantidad de precipitacion obtenida en el rango de tiempo establecido 50/90 mins
                if precipitacion < row.valor_registrado:
                    precipitacion = row.valor_registrado

        a = 10 if precipitacion > 10 else 5 if precipitacion > 5 else 0

        # Variables empleadas por el clasificador ML
        # X datos de información [DENSIDAD,INTENSIDAD]
        X.append([qty, peak_current])
        # y datos de aprendizaje [CANTIDAD DE LLUVIA LEIDA]
        y.append(a)

        # Generar aprendizaje, agregar conocimiento al clf (Clasificador)
        # Si se guarda el modelo, se debe registrar nuevo conocimiento
        if saveModel == True:
            clf.fit(X, y)

        # Información leída para ser clasificada o predicha por ML
        Z = [qty, peak_current]  # DENSIDAD, INTENSIDAD
        # Establece una nueva estructura para el vector
        # Parametros VECTOR, NUEVA FORMA
        # El parametro -1 establece que no se sabe en cuantas columnas debe generar, por lo tanto Numpy se encarga del calculo
        Z = np.reshape(Z, (1, -1))

        # Obtener una prediccion del clasificador
        prediccion = clf.predict(Z)

        # Texto generado para mostrar, dando una conclusion de la lectura
        txt = (
            "En fecha hora " + str(tiempoAnalizarIni) + " se tuvo una intensidad de " + str(
                peak_current) + "A en " + str(
                qty) + " descargas eléctricas en donde luego de 50m a 1:30h se registró una precipitacion de " + str(
                precipitacion) + "mm y la predicción para esta fecha es " + (
                "+=10mm probabilidad de Tormentas severas" if prediccion == 10 else "+=5mm probabilidad de Lluvias muy fuertes" if prediccion == 5 else "+=0 probabilidad baja o nula de lluvias"))

        # Si queremos guardar el analisis en un .csv
        if writeAnalisis == True:
            fileName = str(diaAnalizarIni).replace(":", "").replace(".", "") + "_" + str(diaAnalizarFin).replace(":",
                                                                                                                 "").replace(
                ".", "")
            analisis_data.append([tiempoAnalizarIni, peak_current, qty, precipitacion, prediccion, txt])
            pd.DataFrame(data=analisis_data,
                         columns=['Fecha_Hora', 'Intensidad', 'Densidad', 'Precipitacion_Real', 'Clasificacion',
                                  'Conclusion']).to_csv("analisis/" + fileName + ".csv", sep=";", mode='a', index=False,
                                                        header=False, quoting=csv.QUOTE_NONNUMERIC)

        # Nuevos tiempos a analizar
        tiempoAnalizarIni = tiempoAnalizarFin
        # Sumamos el tiempoIntervalo para continuar con el bucle
        tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)
    # endwhile recorrido de tiempo de analisis


    # Asignamos un tiempo de finalizacion del analisis para saber cuanto demoro
    tiempo_final = time.time()
    tiempo_transcurrido = tiempo_final - inicio_de_tiempo

    print("Tiempo transcurrido de análisis: " + str(tiempo_transcurrido) + " segundos")

    # Si guardamos el modelo
    if saveModel == True:
        # Guardar el modelo en un archivo .sav, puede ser cualquier extension
        joblib.dump(clf, 'modelo.sav')
        # Se guarda en un .csv la información utilizada para generar el modelo, cada vez que se lea de nuevo, se debe usar esta información como conocimiento
        pd.DataFrame(data=X).to_csv('dataset\clf_data.csv', sep=";", mode='w', index=False, header=False)
        pd.DataFrame(data=y).to_csv('dataset\clf_know.csv', sep=";", mode='w', index=False, header=False)

    exit(0)
