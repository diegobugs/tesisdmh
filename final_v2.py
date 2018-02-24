"""

ini.py

Analisando cada descarga que supere los 1000kA o 1000000 amperios en un rango de 45km

Generando poligono de alerta donde vertices son las descargas mas distanciadas

Obteniendo datos de medida de direccion de la celula

"""

import pandas as pd
from util import DatabaseConnection as db
from util import PlotData as plt
from util import MachineLearning as ML
from datetime import datetime
from datetime import timedelta
from scipy.spatial import ConvexHull
import numpy as np
import time
import csv


def CalcularSigtePunto(y1, x1, y2, x2, distancia):
    from math import sin, cos, atan
    # Prueba N 1
    print("x1:" + str(x1) + " y1:" + str(y1))
    print("x2:" + str(x2) + " y2:" + str(y2))
    print("distancia:" + str(distancia))

    xv = x2 - x1
    yv = y2 - y1

    angulo = atan(yv - xv)

    print("angulo: " + str(angulo))

    x = x2 + distancia * sin(angulo)
    y = y2 + distancia * sin(angulo)

    return x, y


def MedirDistancia(lat, lon, latt, lonn):
    from math import sin, cos, sqrt, atan2, radians, atan, degrees

    # approximate radius of earth in km
    R = 6373.0

    lat1 = radians(lat)
    lon1 = radians(lon)
    lat2 = radians(latt)
    lon2 = radians(lonn)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    return distance
    # print("Distancia:", distance)


# Configuraciones por defecto
writeAnalisis = True  # Si queremos crear un .csv con conclusion y resumen del analisis

if __name__ == '__main__':

    SVM = ML.ML_SVM(True)
    plot = plt.Plot()

    inicio_de_tiempo = time.time()
    #  DATOS DE ANALISIS DE PRUEBA
    diaAnalizarIni = datetime.strptime('2015-05-03 06:00:00', '%Y-%m-%d %H:%M:%S')
    diaAnalizarFin = datetime.strptime('2015-05-03 10:00:00', '%Y-%m-%d %H:%M:%S')
    coordenadaAnalizar = '-57.606765,-25.284659'  # Asuncion2
    # coordenadaAnalizar = '-55.873211,-27.336775' # Encarnacion - Playa San Jose

    tiempoIntervalo = 10  # minutos
    # DATOS DE ANALISIS EN TIEMPO REAL

    # diaAnalizarIni = datetime.now() - timedelta(minutes=15)
    # diaAnalizarFin = datetime.now()

    diametroAnalizar = '40000'  # en metros

    tiempoAnalizarIni = diaAnalizarIni
    tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)

    # Conexion a la base de datos de descargas electricas
    database_connection = db.DatabaseConnection('190.128.205.75', 'rayos', 'cta', 'M9vNvgQ2=4os')

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

    analisis_data, ArrayCentroides = [], []
    while tiempoAnalizarIni <= diaAnalizarFin:

        query = 'start_time >="' + datetime.strftime(tiempoAnalizarIni,
                                                     '%Y-%m-%d %H:%M:%S') + '" and start_time<="' + datetime.strftime(
            tiempoAnalizarFin, '%Y-%m-%d %H:%M:%S') + '"'
        datosAnalisis = df.query(query)

        peak_current = 0  # Corriente pico
        densidad = 0

        HoraFinalCelula = None
        HoraInicialCelula = None
        EvoPuntoInicial = []
        EvoPuntoFinal = []
        printPossibleWeather = False
        if not datosAnalisis.empty:

            # Obtenemos las descargas electricas en el tiempo analizado
            for i, row in enumerate(datosAnalisis.itertuples(), 1):
                peak_current += abs(row.peak_current)
                densidad += 1

            # @todo Consultar solamente si se va a generar un nuevo modelo o se va a analizar datos historicos, para tiempo real es inncesesario
            # Consulta de precipitaciones
            # Las precipitaciones obtenidas entre 50 y 90 minutos luego del tiempo de descrgas eléctricas
            query = 'fecha_observacion >="' + datetime.strftime(tiempoAnalizarIni + timedelta(minutes=50),
                                                                '%Y-%m-%d %H:%M:%S') + '" and fecha_observacion < "' + datetime.strftime(
                tiempoAnalizarIni + timedelta(minutes=90), '%Y-%m-%d %H:%M:%S') + '"'
            datosAnalisisPrecip = dfP.query(query)

            # Definición de variables para contar cantidad de estaciones utilizadas
            qtyE = 0  # Cantidad de estaciones usadas
            precipitacion = 0  # Primer precipitacion en 0 por defecto
            if not datosAnalisisPrecip.empty:
                # Bucle de cada precipitacion
                for i, row in enumerate(datosAnalisisPrecip.itertuples(), 1):
                    qtyE += 1
                    # Se obtiene la mayor cantidad de precipitacion obtenida en el rango de tiempo establecido 50/90 mins
                    if precipitacion < row.valor_registrado:
                        precipitacion = row.valor_registrado

            a = 10 if precipitacion >= 10 else 5 if precipitacion >= 5 else 0

            # Predicción del tiempo según densidad e intensidad de descargas electricas en tiempo recorrido
            prediccion = SVM.obtenerPrediccion(densidad, peak_current, a)
            printPossibleWeather = True if prediccion >= 5 else False

            # Si la predicción da como una posible tormenta, se debe plotear la tormenta y su evolución
            if printPossibleWeather:
                # Si supera los 1.000.000 de pico de corriente
                # Generar poligono de los ultimos 90 minutos
                tiempoTormentaIni = tiempoAnalizarIni - timedelta(minutes=90)
                database_connection = db.DatabaseConnection('190.128.205.75', 'rayos', 'cta', 'M9vNvgQ2=4os')
                # rs = database_connection.query(
                #     "SELECT start_time,end_time,type,latitude,longitude,peak_current,ic_height,number_of_sensors,ic_multiplicity,cg_multiplicity,geom FROM lightning_data WHERE type=1 AND ST_DistanceSphere(geom, ST_MakePoint(" + coordenadaAnalizar + ")) <= " + "60000" + "  AND start_time >= to_timestamp('" + str(
                #         diaAnalizarIni) + "', 'YYYY-MM-DD HH24:MI:SS.MS') AND start_time <= to_timestamp('" + str(
                #         diaAnalizarFin) + "', 'YYYY-MM-DD HH24:MI:SS.MS')")
                # dff = pd.DataFrame(data=rs, columns=['start_time', 'end_time', 'type', 'latitude', 'longitude',
                #                                      'peak_current', 'ic_height', 'number_of_sensors',
                #                                      'ic_multiplicity', 'cg_multiplicity', 'geom'])
                #
                # if HoraFinalCelula is None:
                #     HoraFinalCelula = tiempoAnalizarIni
                #
                # # Recorrer estado de tormentas 90 minutos antes
                # ArrayCentroides = []
                # while tiempoTormentaIni <= tiempoAnalizarIni:
                #     tiempoTormentaFin = tiempoTormentaIni + timedelta(minutes=10)
                #     query = 'start_time >="' + datetime.strftime(tiempoTormentaIni,
                #                                                  '%Y-%m-%d %H:%M:%S') + '" and start_time<="' + datetime.strftime(
                #         tiempoTormentaFin, '%Y-%m-%d %H:%M:%S') + '"'
                #     tormentaAnalisis = dff.query(query)
                #     if not datosAnalisis.empty:
                #         fileName = False
                #         points = []
                #         qty = 0
                #         for k, r in enumerate(tormentaAnalisis.itertuples(), 1):
                #             qty += 1
                #             plot.drawIntoMap(r.longitude, r.latitude, r.type)
                #             points.append([r.longitude, r.latitude])
                #             if not fileName:
                #                 # Convertir hora UTC a hora local UTC -3
                #                 horaEvento = r.start_time
                #                 # horaEvento = row.start_time - timedelta(hours=3)
                #                 fileName = str(horaEvento).replace(":", "").replace(".", "")
                #                 fileName = "celula_inicial_" + fileName
                #                 if HoraInicialCelula is None:
                #                     HoraInicialCelula = horaEvento
                #
                #         if fileName:
                #             # points = np.array(points)
                #             points = np.array(points)
                #
                #             if qty >= 3:
                #                 hull = ConvexHull(points, qhull_options="QJ")
                #                 plot.draw(points, hull)
                #                 # Get centroid
                #                 cx = np.mean(hull.points[hull.vertices, 0])
                #                 cy = np.mean(hull.points[hull.vertices, 1])
                #
                #                 if not EvoPuntoInicial:
                #                     EvoPuntoInicial = [cx, cy]
                #
                #                 EvoPuntoFinal = [cx, cy]
                #
                #                 ArrayCentroides.append([cx, cy])
                #
                #                 # Una vez tengamos el centroid debemos ir tomando diferentes poligonos en un lapso de 15-20 minutos atras del 1000000 miliampereos
                #                 # obtener lo sigiente:
                #                 # velocidad segun distancia del primer poligono al ultimo en los 15-20 minutos
                #                 # distancia del futuro punto en 20 minutos
                #                 # angulo de curvatura entre ultimo, anteoultimo y penultimo poligono
                #
                #                 # print("Centroid X:"+str(cx)+" Centroid Y:"+str(cy))
                #                 plot.drawIntoMap(cx, cy, 2)
                #
                #             plot.saveToFile(fileName)
                #             plot = plt.Plot()
                #
                #     tiempoTormentaIni = tiempoTormentaFin

                # print("########")
                # print("Posible evento severo. Amperaje de:", peak_current)
                # plot.drawIntoMap(row.longitude, row.latitude, row.type)
                # # Convertir hora UTC a hora local UTC -3
                # # horaEvento = row.start_time - timedelta(hours=3)
                # # print(horaEvento)
                # fileName = str(row.start_time).replace(":", "").replace(".", "")
                # plot.saveToFile(fileName)
                # plot = plt.Plot()
                # print("Inicio:"+str(EvoPuntoInicial)+" final:"+str(EvoPuntoFinal))

                # fileName = False
                # qty = 0
                # points = []
                # for i, row in enumerate(datosAnalisis.itertuples(), 1):
                #     plot.drawIntoMap(row.longitude, row.latitude, row.type)
                #     qty += 1
                #     points.append([row.longitude, row.latitude])
                #     if not fileName:
                #         # Convertir hora UTC a hora local UTC -3
                #         horaEvento = row.start_time
                #         horaEvento = row.start_time - timedelta(hours=3)
                #         fileName = str(horaEvento).replace(":", "").replace(".", "")
                # points = np.array(points)
                # hull = ConvexHull(points)
                # plot.draw(points, hull)
                #
                # # Get centroid
                # cx = np.mean(hull.points[hull.vertices, 0])
                # cy = np.mean(hull.points[hull.vertices, 1])
                #
                # if ArrayCentroides:
                #     ArrayCentroides.append([cx, cy])
                #
                # # Una vez tengamos el centroid debemos ir tomando diferentes poligonos en un lapso de 15-20 minutos atras del 1000000 miliampereos
                # # obtener lo sigiente:
                # # velocidad segun distancia del primer poligono al ultimo en los 15-20 minutos
                # # distancia del futuro punto en 20 minutos
                # # angulo de curvatura entre ultimo, anteoultimo y penultimo poligono
                #
                # # print("Centroid X:"+str(cx)+" Centroid Y:"+str(cy))
                # plot.drawIntoMap(cx, cy, 2)
                #
                # plot.saveToFile(fileName)
                # plot = plt.Plot()

            # if EvoPuntoFinal and EvoPuntoInicial:
            #     distancia = MedirDistancia(EvoPuntoInicial[0], EvoPuntoInicial[1], EvoPuntoFinal[0], EvoPuntoFinal[1])
            #     if HoraInicialCelula and HoraFinalCelula:
            #         tiempoDesplazamiento = HoraFinalCelula - HoraInicialCelula
            #         tiempoDesplazamiento = tiempoDesplazamiento / timedelta(hours=1)
            #         velocidad = distancia / tiempoDesplazamiento
            #         print("Se desplazó " + str(distancia) + "km en " + str(
            #             tiempoDesplazamiento) + " horas. A una velocidad de " + str(velocidad) + " km/h")
            #
            #         X = [point[0] for point in ArrayCentroides]
            #         X = np.array(X)
            #         Y = [point[1] for point in ArrayCentroides]
            #         Y = np.array(Y)
            #
            #         # Dibujamos los datos para poder visualizarlos y ver si sería lógico
            #         # considerar el ajuste usando un modelo lineal
            #         # plot(X, Y, 'o')
            #
            #         # Para dibujar la recta
            #         plot = plt.Plot()
            #         plot.drawIntoMap(X, Y, 3)
            #
            #         # Calculamos los coeficientes del ajuste (a X + b)
            #         a, b = np.polyfit(X, Y, 1)
            #         # Calculamos el coeficiente de correlación
            #         r = np.corrcoef(X, Y)
            #         # Dibujamos los datos para poder visualizarlos y ver si sería lógico
            #         # considerar el ajuste usando un modelo lineal
            #         # Coordenadas X e Y sobre la recta
            #         (np.max(X), a * np.max(X) + b, '+')
            #
            #         nueva_distancia = velocidad * 0.16  # velocidad de desplazamiento * tiempo esperado de llegada en horas
            #         nuevo_x, nuevo_y = CalcularSigtePunto(np.min(X), a * np.min(X) + b, np.max(X), a * np.max(X) + b,
            #                                               nueva_distancia)
            #         # plot = plt.Plot()
            #         # plot.drawIntoMap(nuevo_x, nuevo_y, 4)
            #         fileName = "punto_futuro"
            #         plot.saveToFile(fileName)
            #         plot = plt.Plot()
            #
            #         print("Se desplazó " + str(distancia) + "km en " + str(
            #             tiempoDesplazamiento) + " horas. A una velocidad de " + str(
            #             velocidad) + " km/h" + " nueva Lat:" + str(nuevo_x) + " Lon:" + str(nuevo_y))

            # Texto generado para mostrar, dando una conclusion de la lectura
            txt = (
                "En fecha hora " + str(tiempoAnalizarIni) + " se tuvo una intensidad de " + str(
                    peak_current) + "A en " + str(
                    densidad) + " descargas eléctricas en donde luego de 50m a 1:30h se registró una precipitacion de " + str(
                    precipitacion) + "mm y la predicción para esta fecha es " + (
                    "+=10mm probabilidad de Tormentas severas" if prediccion == 10 else "+=5mm probabilidad de "
                                                                                        "Lluvias muy fuertes" if
                    prediccion == 5 else "+=0 probabilidad baja o nula de lluvias"))

            # Si queremos guardar el análisis en un .csv
            if writeAnalisis:
                fileName = str(diaAnalizarIni).replace(":", "").replace(".", "") + "_" + str(
                    diaAnalizarFin).replace(":",
                                            "").replace(
                    ".", "")
                analisis_data.append([tiempoAnalizarIni, peak_current, densidad, precipitacion, prediccion, txt])
                pd.DataFrame(data=analisis_data,
                             columns=['Fecha_Hora', 'Intensidad', 'Densidad', 'Precipitacion_Real',
                                      'Clasificacion',
                                      'Conclusion']).to_csv("analisis/" + fileName + ".csv", sep=";", mode='a',
                                                            index=False,
                                                            header=False, quoting=csv.QUOTE_NONNUMERIC)

        tiempoAnalizarIni = tiempoAnalizarFin
        tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)
    # plot.printMap()

    SVM.guardarModelo()

    tiempo_final = time.time()
    tiempo_transcurrido = tiempo_final - inicio_de_tiempo
    print("Tiempo transcurrido de análisis: " + str(tiempo_transcurrido) + " segundos")
    exit(0)

    """"
    1. Recorrer por tipo de descarga
    2. Recorrer mientras tiempo incio sea menor a tiempo final
    3. Sumar tiempo en lapso de 10 minutos
    4. recoger descargas dentro de coordenadas dadas, tipo de rayo y tiempo inicio y fin
    5. Sumar valor absoluto de peak_current
    6. detectar peak_current mayor a 1.000.000 de Amperios        
    """
