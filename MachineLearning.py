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

        self.saveModel = saveModel

        # Definicion por defecto de los .csv de conocimiento
        y = [0, 5, 5, 10, 5,0,0]
        X = [[0, 0], [0, 5], [4, 5], [4, 10], [9, 10],[0,1.2],[9,2]]
        if not os.path.exists('dataset\clf_data.csv'):
            pd.DataFrame(data=X).to_csv('dataset\clf_data.csv', sep=";", mode='w', index=False, header=False)
        if not os.path.exists('dataset\clf_know.csv'):
            pd.DataFrame(data=y).to_csv('dataset\clf_know.csv', sep=";", mode='w', index=False, header=False)

        self.X, self.y = [], []
        with open('dataset\clf_data.csv', 'rt') as clf_data:
            spamreader = csv.reader(clf_data, delimiter=';')
            for row in spamreader:
                self.X.append([float(row[0]), float(row[1])])
        with open('dataset\clf_know.csv', 'rt') as clf_know:
            spamreader = csv.reader(clf_know, delimiter=';')
            for row in spamreader:
                self.y.append(float(row[0]))

        # Definir el aprendizaje
        if self.saveModel == True:
            # Inicializar el clasificador
            self.clf = svm.SVC(kernel='linear', C=1, cache_size=8000, probability=True, class_weight='balanced')
        else:
            # Verificar que exista el modelo
            if os.path.exists('modelo.sav'):
                self.clf = joblib.load('modelo.sav')
            else:
                print("ALERTA: No existe el modelo. Se generará un nuevo modelo.")
                self.saveModel = True
                self.clf = svm.SVC(kernel='linear', C=1, cache_size=8000, probability=True, class_weight='balanced')



    def obtenerPrediccion(self, poligonos, intensidad, clasif=0):

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



        # Generar aprendizaje, agregar conocimiento al clf (Clasificador)
        # Si se guarda el modelo, se debe registrar nuevo conocimiento
        if self.saveModel == True:
            self.clf.fit(self.X, self.y)

        # Información leída para ser clasificada o predicha por ML
        Z = [poligonos, intensidad]  # poligonos, intensidad
        # Establece una nueva estructura para el vector
        # Parametros VECTOR, NUEVA FORMA
        # El parametro -1 establece que no se sabe en cuantas columnas debe generar, por lo tanto Numpy se encarga del calculo
        Z = np.reshape(Z, (1, -1))

        # Obtener una prediccion del clasificador
        prediccion = self.clf.predict(Z)

        # print("poligonos:" +str(poligonos)+" Intensidad:"+str(intensidad)+" Precipitacion:"+str(clasif)+" Predicción:"+str(prediccion))

        return prediccion

    def guardarModelo(self):
        # Guardar el modelo en un archivo .sav, puede ser cualquier extension
        joblib.dump(self.clf, 'modelo.sav')
        # Se guarda en un .csv la información utilizada para generar el modelo, cada vez que se lea de nuevo, se debe usar esta información como conocimiento
        pd.DataFrame(data=self.X).to_csv('dataset\clf_data.csv', sep=";", mode='w', index=False, header=False)
        pd.DataFrame(data=self.y).to_csv('dataset\clf_know.csv', sep=";", mode='w', index=False, header=False)

    def ds(self, diaAnalizarIni, diaAnalizarFin, coordenadaAnalizar, tiempoIntervalo = 10, diametroAnalizar = '45000'):
        self.diaAnalizarIni = diaAnalizarIni  # type: str
        self.diaAnalizarFin = diaAnalizarFin  # type: str
        self.coordenadaAnalizar = coordenadaAnalizar  # type: str (LAT,LON)
        self.tiempoIntervalo = tiempoIntervalo  # type: int minutos
        self.diametroAnalizar = diametroAnalizar  # type: str metros

        diaAnalizarIni = datetime.strptime(diaAnalizarIni, '%Y-%m-%d %H:%M:%S')
        diaAnalizarFin = datetime.strptime(diaAnalizarFin, '%Y-%m-%d %H:%M:%S')

        # Establecer un tiempo de inicio del calculo para saber cuanto demora
        inicio_de_tiempo = time.time()
        print("Analisis iniciado: " + str(datetime.now()))

        # Conexion a la base de datos de descargas electricas
        database_connection = db.DatabaseConnection('190.128.205.75', 'rayos', 'cta', 'M9vNvgQ2=4os')

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

        print("Inicio de bucle")

        analisis_data = []
        peak_currentAux = 0
        nuevaCelula = True
        historialDescargas = [None] * 9
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
                if (qty > 0 or peak_current > 0) and (peak_current > 0):
                    qtyCells = (sum(x is not None for x in historialDescargas))
                    prediccion = self.obtenerPrediccion(qtyCells, peak_current, 0)

                    if prediccion == 10:
                        nuevaCelula = False

            peak_currentAux = peak_current
            # Nuevos tiempos a analizar
            tiempoAnalizarIni = tiempoAnalizarFin
            # Sumamos el tiempoIntervalo para continuar con el bucle
            tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)
        # endwhile recorrido de tiempo de analisis


        # Asignamos un tiempo de finalizacion del analisis para saber cuanto demoro
        tiempo_final = time.time()
        tiempo_transcurrido = tiempo_final - inicio_de_tiempo

        print("score " + str(self.clf.score(self.X, self.y)))

        print("Tiempo transcurrido de análisis: " + str(tiempo_transcurrido) + " segundos")


    def svm(self, diaAnalizarIni, diaAnalizarFin, coordenadaAnalizar, tiempoIntervalo = 10, diametroAnalizar = '45000'):
        self.diaAnalizarIni = diaAnalizarIni  # type: str
        self.diaAnalizarFin = diaAnalizarFin  # type: str
        self.coordenadaAnalizar = coordenadaAnalizar  # type: str (LAT,LON)
        self.tiempoIntervalo = tiempoIntervalo  # type: int minutos
        self.diametroAnalizar = diametroAnalizar  # type: str metros

        diaAnalizarIni = datetime.strptime(diaAnalizarIni, '%Y-%m-%d %H:%M:%S')
        diaAnalizarFin = datetime.strptime(diaAnalizarFin, '%Y-%m-%d %H:%M:%S')

        # Establecer un tiempo de inicio del calculo para saber cuanto demora
        inicio_de_tiempo = time.time()
        print("Analisis iniciado: " + str(datetime.now()))

        # Conexion a la base de datos de descargas electricas
        database_connection = db.DatabaseConnection('190.128.205.75', 'rayos', 'cta', 'M9vNvgQ2=4os')

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

        print("Inicio de bucle")

        analisis_data = []
        peak_currentAux = 0
        nuevaCelula = True
        historialDescargas = [None] * 9
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
                if (qty > 0 or peak_current > 0) and (peak_current > 0):
                    qtyCells = (sum(x is not None for x in historialDescargas))
                    prediccion = self.obtenerPrediccion(qtyCells, peak_current, 0)

                    if prediccion == 10:
                        nuevaCelula = False

            peak_currentAux = peak_current
            # Nuevos tiempos a analizar
            tiempoAnalizarIni = tiempoAnalizarFin
            # Sumamos el tiempoIntervalo para continuar con el bucle
            tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)
        # endwhile recorrido de tiempo de analisis


        # Asignamos un tiempo de finalizacion del analisis para saber cuanto demoro
        tiempo_final = time.time()
        tiempo_transcurrido = tiempo_final - inicio_de_tiempo

        print("score " + str(self.clf.score(self.X, self.y)))

        print("Tiempo transcurrido de análisis: " + str(tiempo_transcurrido) + " segundos")

    def RecorrerYGenerar(self, diaAnalizarIni, diaAnalizarFin, coordenadaAnalizar, tiempoIntervalo = 10, diametroAnalizar = '45000'):
        self.diaAnalizarIni = diaAnalizarIni # type: str
        self.diaAnalizarFin = diaAnalizarFin # type: str
        self.coordenadaAnalizar = coordenadaAnalizar  # type: str (LAT,LON)
        self.tiempoIntervalo = tiempoIntervalo  # type: int minutos
        self.diametroAnalizar = diametroAnalizar  # type: str metros

        diaAnalizarIni = datetime.strptime(diaAnalizarIni, '%Y-%m-%d %H:%M:%S')
        diaAnalizarFin = datetime.strptime(diaAnalizarFin, '%Y-%m-%d %H:%M:%S')


        # Parametros para buscar descargas
        # diaAnalizarIni = datetime.strptime('2015-05-03 06:00:00', '%Y-%m-%d %H:%M:%S')
        # diaAnalizarFin = datetime.strptime('2015-05-03 10:00:00', '%Y-%m-%d %H:%M:%S')
        # coordenadaAnalizar = '-57.606765,-25.284659'  # Asuncion2
        # tiempoIntervalo = 10  # minutos
        # diametroAnalizar = '40000'  # en metros

        # Establecer un tiempo de inicio del calculo para saber cuanto demora
        inicio_de_tiempo = time.time()
        print("Analisis iniciado: " + str(datetime.now()))

        # Conexion a la base de datos de descargas electricas
        database_connection = db.DatabaseConnection('190.128.205.75', 'rayos', 'cta', 'M9vNvgQ2=4os')

        # Definicion de tiempos a ser analizados, estas variables iran iterando en un bucle segun el tiempoIntervalo
        tiempoAnalizarIni = diaAnalizarIni
        tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)

        print("Conectando a la base de datos...Descargas")

        print(coordenadaAnalizar)

        rows = database_connection.query("SELECT start_time,end_time,type,latitude,longitude,peak_current,ic_height,number_of_sensors,ic_multiplicity,cg_multiplicity,geom FROM lightning_data WHERE type=1 AND ST_DistanceSphere(geom, ST_MakePoint(" + coordenadaAnalizar + ")) <= " + diametroAnalizar + "  AND start_time >= to_timestamp('" + str(diaAnalizarIni) + "', 'YYYY-MM-DD HH24:MI:SS.MS') AND start_time <= to_timestamp('" + str(diaAnalizarFin) + "', 'YYYY-MM-DD HH24:MI:SS.MS')")
        print("Conectado")

        print("Preparando datos")
        df = pd.DataFrame(data=rows,
                          columns=['start_time', 'end_time', 'type', 'latitude', 'longitude', 'peak_current', 'ic_height',
                                   'number_of_sensors', 'ic_multiplicity', 'cg_multiplicity', 'geom'])

        if self.saveModel == True:
            # Conexion con base de datos de precipitaciones
            database_connection = db.DatabaseConnection('precip', 'precip', 'postgres', '12345')
            print("Conectando a la base de datos...Precipitaciones")
            estaciones = "86218,86217,86214,86206,86207,86201"
            # estaciones = "86246,86248"
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

        analisis_data = []
        peak_currentAux = 0
        nuevaCelula = True
        historialDescargas = [None] * 9
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
            peak_current = round(peak_current,1)
            # peak_current = math.ceil(peak_current / 10000) * 10000


            precipitacion = 0  # Primer precipitacion en 0 por defecto
            a = 0

            # # Consulta de precipitaciones
            # # Las precipitaciones obtenidas entre 50 y 90 minutos luego del tiempo de descrgas eléctricas
            query = 'fecha_observacion >="' + datetime.strftime(tiempoAnalizarIni + timedelta(minutes=50),
                                                                '%Y-%m-%d %H:%M:%S') + '" and fecha_observacion <= "' + datetime.strftime(
                tiempoAnalizarIni + timedelta(minutes=70), '%Y-%m-%d %H:%M:%S') + '"'
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




            if histLatLon:
                for idx, item in enumerate(historialDescargas):
                    historialDescargas.insert(idx, histLatLon)
                    historialDescargas.pop()
                    break

            # Una vez dada la predicción de 10 = tormenta
            # Esperar a que peak_current sea menor o igual a 50000 es decir, que sea otra ceula de tormenta, no la misma
            # Ya que la misma celula puede mostrar una intensidad de 2M , 3M, 4M de amperios pero ya no indicar que luego de 1h lloverá +=10mm
            if self.saveModel and peak_current <= 1:
                nuevaCelula = True
                historialDescargas = [None] * 9

            if nuevaCelula or self.saveModel==False:
                qtyCells = (sum(x is not None for x in historialDescargas))
                if (qtyCells>0 or peak_current>0 or precipitacion > 0) and (precipitacion>0.6 or peak_current > 0) and (precipitacion>0 and peak_current>0):
                # if 1==1:
                    a = 10 if (precipitacion >= 10 and peak_current > 8 and qtyCells <= 4) else 5 if (precipitacion >= 5) else 0
                    # if a==0 and precipitacion>=10:
                    #     a=10

                    # a = 10 if (precipitacion >= 10 and peak_current > 0.1) else 5 if (precipitacion >= 5) else 0
                    if peak_current == 0:
                        a = 0

                    prediccion = self.obtenerPrediccion(qtyCells,peak_current,a)


                    if self.saveModel and prediccion==10 and precipitacion > 9:
                        nuevaCelula = False

                    # Texto generado para mostrar, dando una conclusion de la lectura
                    txt = (
                        "En fecha hora " + str(tiempoAnalizarIni) + " se tuvo una intensidad de " + str(
                            peak_current) + "A en " + str(
                            qtyCells) + " descargas eléctricas en donde luego de 50m a 1:30h se registró una precipitacion de " + str(
                            precipitacion) + "mm y la predicción para esta fecha es " + (
                            "+=10mm probabilidad de Tormentas severas" if prediccion == 10 else "+=5mm probabilidad de Lluvias muy fuertes" if prediccion == 5 else "+=0 probabilidad baja o nula de lluvias"))


                    analisis_data.append([tiempoAnalizarIni, peak_current, qtyCells, precipitacion, prediccion, txt])

                    print("Fecha/hora:"+str(tiempoAnalizarIni)+" Intensidad:"+str(peak_current)+" poligonos:"+str(qtyCells)+" Precipitacion:"+str(precipitacion)+" Predicción:"+ ("Tormenta" if prediccion==10 else "Lluvia" if prediccion==5 else "Nada"))

            peak_currentAux = peak_current
            # Nuevos tiempos a analizar
            tiempoAnalizarIni = tiempoAnalizarFin
            # Sumamos el tiempoIntervalo para continuar con el bucle
            tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)
        # endwhile recorrido de tiempo de analisis


        # Asignamos un tiempo de finalizacion del analisis para saber cuanto demoro
        tiempo_final = time.time()
        tiempo_transcurrido = tiempo_final - inicio_de_tiempo

        # Si queremos guardar el analisis en un .csv
        fileName = str(diaAnalizarIni).replace(":", "").replace(".", "") + "_" + str(diaAnalizarFin).replace(":",
                                                                                                             "").replace(
            ".", "")

        analisis_data.append(["Tiempo transcurrido de análisis: " + str(tiempo_transcurrido) + " segundos", '','','','',''])

        pd.DataFrame(data=analisis_data,
                     columns=['Fecha_Hora', 'Intensidad', 'poligonos', 'Precipitacion_Real', 'Clasificacion',
                              'Conclusion']).to_csv("analisis/" + fileName + ".csv", sep=";", mode='a', index=False,
                                                    header=False, quoting=csv.QUOTE_NONNUMERIC)

        print("score "+str(self.clf.score(self.X, self.y)))

        # Si guardamos el modelo
        if self.saveModel == True:
            self.guardarModelo()

        print("Tiempo transcurrido de análisis: " + str(tiempo_transcurrido) + " segundos")