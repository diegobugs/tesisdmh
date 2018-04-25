"""

ini.py

Analisando cada descarga que supere los 1000kA o 1000000 amperios en un rango de 45km

Generando poligono de alerta donde vertices son las descargas mas distanciadas

Obteniendo datos de medida de direccion de la celula

"""

import csv
import glob
import os.path
import time
from datetime import datetime
from datetime import timedelta

import moviepy.editor as mpy
import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull

import MachineLearning as ML
from util import DatabaseConnection as db
from util import PlotData as plt
from util import PlotOnMap

import json


def SVM(diaAnalizarIni, diaAnalizarFin, coordenadaAnalizar):
    SVM = ML.ML_SVM(False)
    tormentaDetectada = False
    inicio_de_tiempo = time.time()
    #  DATOS DE ANALISIS DE PRUEBA
    diaAnalizarIni = datetime.strptime(diaAnalizarIni, '%Y-%m-%d %H:%M:%S')
    diaAnalizarFin = datetime.strptime(diaAnalizarFin, '%Y-%m-%d %H:%M:%S')
    # coordenadaAnalizar = '-57.606765,-25.284659'  # Asuncion
    # coordenadaAnalizar = '-55.873211,-27.336775' # Encarnacion - Playa San Jose

    tiempoIntervalo = 10  # minutos
    # DATOS DE ANALISIS EN TIEMPO REAL

    # diaAnalizarIni = datetime.now() - timedelta(minutes=15)
    # diaAnalizarFin = datetime.now()

    diametroAnalizar = '45000'  # en metros

    # Definicion de tiempos a ser analizados, estas variables iran iterando en un bucle segun el tiempoIntervalo
    tiempoAnalizarIni = diaAnalizarIni
    tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)

    print("Conectando a la base de datos...Descargas")
    # Conexion a la base de datos de descargas electricas
    database_connection = db.DatabaseConnection('190.128.205.75', 'rayos', 'cta', 'M9vNvgQ2=4os')
    rows = database_connection.query(
        "SELECT start_time,end_time,type,latitude,longitude,peak_current,ic_height,number_of_sensors,ic_multiplicity,cg_multiplicity,geom FROM lightning_data WHERE type=1 AND ST_DistanceSphere(geom, ST_MakePoint(" + coordenadaAnalizar + ")) <= " + diametroAnalizar + "  AND start_time >= to_timestamp('" + str(
            diaAnalizarIni) + "', 'YYYY-MM-DD HH24:MI:SS.MS') AND start_time <= to_timestamp('" + str(
            diaAnalizarFin) + "', 'YYYY-MM-DD HH24:MI:SS.MS')")
    print("Conectado")

    print("Preparando datos")
    df = pd.DataFrame(data=rows,
                      columns=['start_time', 'end_time', 'type', 'latitude', 'longitude', 'peak_current', 'ic_height',
                               'number_of_sensors', 'ic_multiplicity', 'cg_multiplicity', 'geom'])

    print("Inicio de bucle")

    analisis_data, ArrayCentroides = [], []
    historialDescargas = [None] * 9
    printPossibleWeather = False
    while tiempoAnalizarIni <= diaAnalizarFin:

        plot = plt.Plot()

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

        histLatLon = []
        if not datosAnalisis.empty:

            # Obtenemos las descargas eléctricas en el tiempo analizado
            for i, row in enumerate(datosAnalisis.itertuples(), 1):
                peak_current += abs(row.peak_current)
                histLatLon.append([row.latitude,row.longitude])
                densidad += 1

            # poner los valores en base 100000, Ej: 1.000.000 = 10
            peak_current = peak_current / 100000
            peak_current = round(peak_current, 1)


            if histLatLon:
                for idx, item in enumerate(historialDescargas):
                    historialDescargas.insert(idx, histLatLon)
                    historialDescargas.pop()
                    break

            # Si hablamos de otra celula, resetamos el historico de descargas
            if peak_current <= 0.5:
                historialDescargas = [None] * 9

            qtyCells = (sum(x is not None for x in historialDescargas))

            # Obtenemos la predicción generada por MachineLearning.py
            prediccion = SVM.obtenerPrediccion(qtyCells, peak_current)

            printPossibleWeather = True if prediccion == 10 else False

            # Si la predicción da como una posible tormenta, se debe plotear la tormenta y su evolución
            if printPossibleWeather:

                # Si supera los 1.000.000 de pico de corriente
                # Generar poligono de los ultimos 90 minutos, o de los ultimos 9 registros consultados

                if HoraFinalCelula is None:
                    HoraFinalCelula = tiempoAnalizarIni


                ArrayCentroides = []


                if qtyCells <= 4:
                    print(str(tiempoAnalizarFin)+" tormenta en 1h "+str(tiempoAnalizarFin + timedelta(minutes=60)))
                    tormentaDetectada = True


                # if qtyCells >= 8:
                if qtyCells >= 3:
                    # Recorrer estado de tormentas 90 minutos antes
                    for idx, item in enumerate(historialDescargas):
                        fileName = str(tiempoAnalizarFin).replace(":", "").replace(".", "")
                        fileName = "CELULA_"+fileName+str(idx)
                        # plotCel = plt.Plot()
                        plotGeo = PlotOnMap.PlotOnGeoJSON()
                        points = []



                        if item is not None:
                            for k, r in enumerate(item):
                                # plotCel.drawIntoMap(r[1], r[0], 1)
                                # plotGeo.addFeature(r[1], r[0])
                                points.append([r[1], r[0]])

                        # Si hay descargas eléctricas
                        saveFile = False

                        if points and len(points) >= 3:
                            saveFile = True
                            points = np.array(points)

                            # Generamos un poligono que contenga todas las descargas electricas
                            hull = ConvexHull(points, qhull_options="QJ")
                            # plotCel.draw(points, hull)
                            plotGeo.draw(points,hull)


                            # Obtenemos el centroide de nuestro poligono
                            cx = np.mean(hull.points[hull.vertices, 0])
                            cy = np.mean(hull.points[hull.vertices, 1])

                            # Si no existe un punto inicial de la tormenta, asignamos
                            if not EvoPuntoInicial:
                                EvoPuntoInicial = [cx, cy]

                            # El punto final de nuestra tormenta es el ultimo dato consultado
                            EvoPuntoFinal = [cx, cy]

                            # Generamos un array con todos nuestros centroides
                            ArrayCentroides.append([cx, cy])

                            # Dibujamos los centroides en el mapa
                            # plotCel.drawIntoMap(cx, cy, 2)
                            plotGeo.addFeature(cx,cy)


                        # Imprimimos en una imagen cada una de las 9 celulas
                        if saveFile:
                            # plotCel.saveToFile(fileName)
                            fc = plotGeo.getFeatureCollection()
                            plotGeo.dumpGeoJson(fc, fileName+'.geojson')

            # Si tenemos un inicio y un fin de nuestra tormenta
            if EvoPuntoFinal and EvoPuntoInicial and ArrayCentroides:
                # distancia = MedirDistancia(EvoPuntoInicial[0], EvoPuntoInicial[1], EvoPuntoFinal[0], EvoPuntoFinal[1])
                # if HoraInicialCelula and HoraFinalCelula:
                #     tiempoDesplazamiento = HoraFinalCelula - HoraInicialCelula
                #     tiempoDesplazamiento = tiempoDesplazamiento / timedelta(hours=1)
                #     velocidad = distancia / tiempoDesplazamiento
                #     print("Se desplazó " + str(distancia) + "km en " + str(
                #         tiempoDesplazamiento) + " horas. A una velocidad de " + str(velocidad) + " km/h")

                X = [point[0] for point in ArrayCentroides]
                X = np.array(X)
                Y = [point[1] for point in ArrayCentroides]
                Y = np.array(Y)

                # Dibujamos los datos para poder visualizarlos y ver si sería lógico
                # considerar el ajuste usando un modelo lineal
                # plot(X, Y, 'o')

                # Para dibujar la recta
                fileName = str(tiempoAnalizarFin).replace(":", "").replace(".", "")
                fileName = "RECTA_" + fileName
                plotRecta = PlotOnMap.PlotOnGeoJSON()
                plotRecta.makePath(X, Y)
                fc = plotRecta.getFeatureCollection()
                plotRecta.dumpGeoJson(fc, fileName + '.geojson')

                # Calculamos los coeficientes del ajuste (a X + b)
                a, b = np.polyfit(X, Y, 1)
                # Calculamos el coeficiente de correlación
                r = np.corrcoef(X, Y)
                # Dibujamos los datos para poder visualizarlos y ver si sería lógico
                # considerar el ajuste usando un modelo lineal
                # Coordenadas X e Y sobre la recta
                (np.max(X), a * np.max(X) + b, '+')

                # nueva_distancia = velocidad * 0.16  # velocidad de desplazamiento * tiempo esperado de llegada en horas
                # nuevo_x, nuevo_y = CalcularSigtePunto(np.min(X), a * np.min(X) + b, np.max(X), a * np.max(X) + b,
                #                                       nueva_distancia)
                # # plot = plt.Plot()
                # # plot.drawIntoMap(nuevo_x, nuevo_y, 4)
                # fileName = "punto_futuro"
                #
                # plot.saveToFile(fileName)
                # plot = plt.Plot()
                #
                # print("Se desplazó " + str(distancia) + "km en " + str(
                #     tiempoDesplazamiento) + " horas. A una velocidad de " + str(
                #     velocidad) + " km/h" + " nueva Lat:" + str(nuevo_x) + " Lon:" + str(nuevo_y))

            # Texto generado para mostrar, dando una conclusion de la lectura
            txt = (
                "En fecha hora " + str(tiempoAnalizarIni) + " se tuvo una intensidad de " + str(peak_current) + "A en " + str(densidad) + " descargas eléctricas en donde luego de 50m a 1h:10m la predicción es " + ("+=10mm probabilidad de Tormentas severas" if prediccion == 10 else "+=5mm probabilidad de Lluvias muy fuertes" if prediccion == 5 else "+=0 probabilidad baja o nula de lluvias"))
            analisis_data.append([tiempoAnalizarIni, peak_current, densidad, prediccion, txt])



        tiempoAnalizarIni = tiempoAnalizarFin
        tiempoAnalizarFin = tiempoAnalizarFin + timedelta(minutes=tiempoIntervalo)
    # plot.printMap()

    # SVM.guardarModelo()

    video_name = './png/tormenta'  ##nombre del archivo
    # if os.path.exists('png/RECTA*.png'):
    #     fps = 1
    #     file_list = glob.glob('./png/RECTA*.png')  # obtiene los png de la ruta actual
    #     # list.sort(file_list, key=lambda x: int(x.split('_')[1].split('.png')[0])) # Sort the images by #, this may need to be tweaked for your use case
    #     clip = mpy.ImageSequenceClip(file_list, fps=fps)
    #     clip.write_videofile('{}.mp4'.format(video_name), fps=fps)

    tiempo_final = time.time()
    tiempo_transcurrido = tiempo_final - inicio_de_tiempo
    print("Tiempo transcurrido de análisis: " + str(tiempo_transcurrido) + " segundos")


    return {'tormenta': tormentaDetectada, 'src': video_name+".mp4", 'tiempo': tiempo_transcurrido}



    """"
    1. Recorrer por tipo de descarga
    2. Recorrer mientras tiempo incio sea menor a tiempo final
    3. Sumar tiempo en lapso de 10 minutos
    4. recoger descargas dentro de coordenadas dadas, tipo de rayo y tiempo inicio y fin
    5. Sumar valor absoluto de peak_current
    6. detectar peak_current mayor a 1.000.000 de Amperios        
    """
