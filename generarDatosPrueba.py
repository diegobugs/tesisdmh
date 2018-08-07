import pandas as pd
from util import DatabaseConnection as db
from datetime import datetime
from datetime import timedelta
import numpy as np
import time
from sklearn.externals import joblib
from sklearn import svm
import os.path
import csv
import math

# Configuraciones por defecto
# writeAnalisis = False  # Si queremos crear un .csv con conclusion y resumen del analisis
# saveModel = False  # Si queremos guardar el modelo


class ML_SVM:
    def __init__(self, saveModel=False):

        # Definicion por defecto de los .csv de conocimiento
        y = []
        X = []
        if not os.path.exists('dataset\\test_data.csv'):
            pd.DataFrame(data=X).to_csv('dataset\\test_data.csv', sep=";", mode='w', index=False, header=False)
        if not os.path.exists('dataset\\test_know.csv'):
            pd.DataFrame(data=y).to_csv('dataset\\test_know.csv', sep=";", mode='w', index=False, header=False)

        self.X, self.y = [], []
        with open('dataset\\test_data.csv', 'rt') as test_data:
            spamreader = csv.reader(test_data, delimiter=';')
            for row in spamreader:
                self.X.append([float(row[0]), float(row[1])])
        with open('dataset\\test_know.csv', 'rt') as test_know:
            spamreader = csv.reader(test_know, delimiter=';')
            for row in spamreader:
                self.y.append(float(row[0]))


    def agregarDatos(self, poligonos, intensidad, clasif=0):

        intensidad = intensidad # type: int
        poligonos = poligonos # type: int
        clasif = clasif # type: int

        # Variables empleadas por el clasificador ML
        # X datos de información [intensidad,poligonos]
        self.X.append([poligonos, intensidad])
        # y datos de aprendizaje [CANTIDAD DE LLUVIA LEIDA]
        self.y.append(clasif)


        # Ordenar X
        matrix = np.matrix(np.column_stack((self.X, self.y)))
        matrix = matrix[np.argsort(matrix.A[:, 1])]

        self.X = (np.delete(matrix, np.s_[2], axis=1)).tolist()
        y = ((np.delete(matrix, np.s_[0:2], axis=1)).ravel()).tolist()
        self.y = y[0]


    def guardarDatos(self):
        # Se guarda en un .csv la información utilizada para generar el modelo, cada vez que se lea de nuevo, se debe usar esta información como conocimiento
        pd.DataFrame(data=self.X).to_csv('dataset\\test_data.csv', sep=";", mode='w', index=False, header=False)
        pd.DataFrame(data=self.y).to_csv('dataset\\test_know.csv', sep=";", mode='w', index=False, header=False)

    def svm(self, diaAnalizarIni, diaAnalizarFin, coordenadaAnalizar, tiempoIntervalo = 10, diametroAnalizar = '45000'):
        self.diaAnalizarIni = diaAnalizarIni  # type: str
        self.diaAnalizarFin = diaAnalizarFin  # type: str
        self.coordenadaAnalizar = coordenadaAnalizar  # type: str (LAT,LON)
        self.tiempoIntervalo = tiempoIntervalo  # type: int minutos
        self.diametroAnalizar = diametroAnalizar  # type: str metros

        diaAnalizarFin = datetime.strptime(diaAnalizarFin, '%Y-%m-%d %H:%M:%S')
        diaAnalizarIni = datetime.strptime(diaAnalizarIni, '%Y-%m-%d %H:%M:%S')
        # diaAnalizarIni = diaAnalizarFin - timedelta(minutes=90)

        # Establecer un tiempo de inicio del calculo para saber cuanto demora
        inicio_de_tiempo = time.time()
        print("Analisis iniciado: " + str(datetime.now()))

        # Conexion a la base de datos de descargas electricas
        database_connection = db.DatabaseConnection('', 'rayos', 'cta', '')

        # Definicion de tiempos a ser analizados, estas variables iran iterando en un bucle segun el tiempoIntervalo
        tiempoAnalizarIni = diaAnalizarIni
        tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)

        print("Conectando a la base de datos...Descargas")

        print(coordenadaAnalizar)

        rows = database_connection.query(
            "SELECT start_time,end_time,type,latitude,longitude,peak_current,ic_height,number_of_sensors,ic_multiplicity,cg_multiplicity,geom FROM lightning_data WHERE type=1 AND ST_DistanceSphere(geom, ST_MakePoint(" + coordenadaAnalizar + ")) <= " + diametroAnalizar + "  AND start_time >= to_timestamp('" + str(
                diaAnalizarIni) + "', 'YYYY-MM-DD HH24:MI:SS.MS') AND start_time <= to_timestamp('" + str(
                diaAnalizarFin) + "', 'YYYY-MM-DD HH24:MI:SS.MS')")
        print("Conectado")

        print("Preparando datos")
        df = pd.DataFrame(data=rows,
                          columns=['start_time', 'end_time', 'type', 'latitude', 'longitude', 'peak_current',
                                   'ic_height',
                                   'number_of_sensors', 'ic_multiplicity', 'cg_multiplicity', 'geom'])

        # Conexion con base de datos de precipitaciones
        database_connection = db.DatabaseConnection('localhost', 'precip', 'postgres', '12345')
        print("Conectando a la base de datos...Precipitaciones")
        estaciones = "86218,86217,86214,86206,86207,86201" # Asuncion
        # estaciones = "86246,86248" #Ciudad del este
        rows = database_connection.query(
            "SELECT codigo_estacion,nombre_estacion,latitud,longitud,fecha_observacion,valor_registrado,valor_corregido FROM precipitacion WHERE codigo_estacion IN (" + estaciones + ") AND fecha_observacion >= to_timestamp('" + str(
                diaAnalizarIni) + "', 'YYYY-MM-DD HH24:MI:SS.MS') AND fecha_observacion <= to_timestamp('" + str(
                diaAnalizarFin) + "', 'YYYY-MM-DD HH24:MI:SS.MS')")
        print("Conectado")

        print("Preparando datos")
        dfP = pd.DataFrame(data=rows,
                           columns=['codigo_estacion', 'nombre_estacion', 'latitud', 'longitud', 'fecha_observacion',
                                    'valor_registrado', 'valor_corregido'])

        print(dfP.count())

        print("Inicio de bucle")

        analisis_data = []
        peak_currentAux = 0
        nuevaCelula = True
        historialDescargas = [None] * 9
        a = 0
        while tiempoAnalizarIni <= diaAnalizarFin:
            query = 'start_time >="' + datetime.strftime(tiempoAnalizarIni,
                                                         '%Y-%m-%d %H:%M:%S') + '" and start_time<="' + datetime.strftime(
                tiempoAnalizarFin, '%Y-%m-%d %H:%M:%S') + '"'
            datosAnalisis = df.query(query)

            peak_current = 0  # Corriente pico INTENSIDAD
            qty = 0  # Cantidad de rayos poligonos

            # Si el dataset de descargas no se encuentra vacío\
            histLatLon = []
            if not datosAnalisis.empty:
                # Bucle de cada rayo

                # Obtener INTENSIDAD Y poligonos
                for i, row in enumerate(datosAnalisis.itertuples(), 1):
                    histLatLon.append([row.latitude, row.longitude])
                    peak_current += abs(row.peak_current)
                    qty += 1
                    # endfor
            # endif hay datos de descargas

            # poner los valores en base 100000, Ej: 1.000.000 = 10
            peak_current = peak_current / 100000
            peak_current = round(peak_current, 1)
            # peak_current = math.ceil(peak_current / 10000) * 10000

            precipitacion = 0  # Primer precipitacion en 0 por defecto

            # # Consulta de precipitaciones
            # # Las precipitaciones obtenidas entre 50 y 90 minutos luego del tiempo de descrgas eléctricas
            query = 'fecha_observacion >="' + datetime.strftime(tiempoAnalizarIni + timedelta(minutes=40),
                                                                '%Y-%m-%d %H:%M:%S') + '" and fecha_observacion <= "' + datetime.strftime(
                tiempoAnalizarIni + timedelta(minutes=70), '%Y-%m-%d %H:%M:%S') + '"'
            datosAnalisis = dfP.query(query)

            if not datosAnalisis.empty:
                # Bucle de cada precipitacion
                for i, row in enumerate(datosAnalisis.itertuples(), 1):
                    # Se obtiene la mayor cantidad de precipitacion obtenida en el rango de tiempo establecido 50/90 mins
                    if precipitacion < row.valor_registrado:
                        precipitacion = row.valor_registrado

            if histLatLon:
                for idx, item in enumerate(historialDescargas):
                    historialDescargas.insert(idx, histLatLon)
                    historialDescargas.pop()
                    break

            # Una vez dada la predicción de 10 = tormenta
            # Esperar a que peak_current sea menor o igual a 50000 es decir, que sea otra ceula de tormenta, no la misma
            # Ya que la misma celula puede mostrar una intensidad de 2M , 3M, 4M de amperios pero ya no indicar que luego de 1h lloverá +=10mm
            if peak_current <= 0.5:
                nuevaCelula = True
                historialDescargas = [None] * 9

            if nuevaCelula:
                qtyCells = (sum(x is not None for x in historialDescargas))
                if (qtyCells > 0 or peak_current > 0 or precipitacion > 0) and (precipitacion > 0.6 or peak_current > 0) and (precipitacion > 0 and peak_current > 0):

                    # a = 10 if (precipitacion >= 10 and peak_current > 5 and qtyCells <= 4) else 5 if (
                    # precipitacion >= 5) else 0
                    # if a == 0 and precipitacion >= 10:
                    #     a = 10
                    a=0
                    if precipitacion >= 10 and peak_current >= 10 and qtyCells <=4:
                        a = 10
                    else:
                        a = 5

                    if precipitacion < 5:
                        a = 0

                    prediccion = self.agregarDatos(qtyCells, peak_current, a)

                    if a == 10:
                        nuevaCelula = False

                    # Texto generado para mostrar, dando una conclusion de la lectura
                    txt = (
                        "En fecha hora " + str(tiempoAnalizarIni) + " se tuvo una intensidad de " + str(
                            peak_current) + "A en " + str(
                            qtyCells) + " poligonos. Luego de 50m a 80min se registró una precipitacion de " + str(
                            precipitacion) + "mm y la predicción para esta fecha es " + (
                            "+=10mm probabilidad de Tormentas severas" if a == 10 else "+=5mm probabilidad de Lluvias muy fuertes" if a == 5 else "+=0 probabilidad baja o nula de lluvias"))

                    print(txt)

            peak_currentAux = peak_current
            # Nuevos tiempos a analizar
            tiempoAnalizarIni = tiempoAnalizarFin
            # Sumamos el tiempoIntervalo para continuar con el bucle
            tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)
        # endwhile recorrido de tiempo de analisis

        self.guardarDatos()
