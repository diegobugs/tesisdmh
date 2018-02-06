
"""

analisis_V2

Analisando cada descarga que supere los 1000kA o 1000000 amperios en un rango de 45km

Generando poligono de alerta donde vertices son las descargas mas distanciadas

Obteniendo datos de medida de direccion de la celula

"""

import pandas as pd
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from util import DatabaseConnection as db
from util import PlotData as plt
from datetime import datetime
from datetime import timedelta
from scipy.spatial import ConvexHull
import numpy as np
import time


def CalcularSigtePunto(y1,x1,y2,x2, distancia):
    from math import sin,cos,atan
    # Prueba N 1
    print("x1:"+str(x1)+" y1:"+str(y1))
    print("x2:"+str(x2)+" y2:"+str(y2))
    print("distancia:"+str(distancia))

    xv = x2 - x1
    yv = y2 - y1

    angulo = atan(yv - xv)

    print("angulo: "+str(angulo))

    x = x2 + distancia * sin(angulo)
    y = y2 + distancia * sin(angulo)

    return x,y

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


if __name__ == '__main__':

    plot = plt.Plot()
    # plot.drawIntoMap(-57.623154, -25.280073,1)
    # plot.drawIntoMap(-57.603154, -25.284073, 1)
    # plot.printMap()
    # exit(0)
    inicio_de_tiempo = time.time()
    database_connection = db.DatabaseConnection()
    #  DATOS DE ANALISIS DE PRUEBA
    diaAnalizarIni = datetime.strptime('2016-11-19 13:00:00', '%Y-%m-%d %H:%M:%S')
    diaAnalizarFin = datetime.strptime('2016-11-19 18:56:59', '%Y-%m-%d %H:%M:%S')
    # coordenadaAnalizar = '-57.606765,-25.284659' # Asuncion
    coordenadaAnalizar = '-55.873211,-27.336775' # Encarnacion - Playa San Jose

    tiempoIntervalo = 10  # minutos
    # DATOS DE ANALISIS EN TIEMPO REAL

    # diaAnalizarIni = datetime.now() - timedelta(minutes=15)
    # diaAnalizarFin = datetime.now()

    diametroAnalizar = '45000' #en metros



    tiempoAnalizarIni = diaAnalizarIni
    tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)

    rows = database_connection.query(
        "SELECT start_time,end_time,type,latitude,longitude,peak_current,ic_height,number_of_sensors,ic_multiplicity,cg_multiplicity,geom FROM lightning_data WHERE type=1 AND ST_DistanceSphere(geom, ST_MakePoint(" + coordenadaAnalizar + ")) <= " + diametroAnalizar + "  AND start_time >= to_timestamp('" + str(diaAnalizarIni) + "', 'YYYY-MM-DD HH24:MI:SS.MS') AND start_time <= to_timestamp('" + str(diaAnalizarFin) + "', 'YYYY-MM-DD HH24:MI:SS.MS')")
    df = pd.DataFrame(data=rows, columns=['start_time','end_time','type','latitude','longitude','peak_current','ic_height','number_of_sensors','ic_multiplicity','cg_multiplicity','geom'])

    while tiempoAnalizarIni <= diaAnalizarFin:

        query = 'start_time >="'+datetime.strftime(tiempoAnalizarIni, '%Y-%m-%d %H:%M:%S')+'" and start_time<="'+datetime.strftime(tiempoAnalizarFin, '%Y-%m-%d %H:%M:%S')+'"'
        # query = 'start_time >="'+strd1+'" and start_time <= "'+strd2+'"'

        # query = 'start_time >="2016-12-19 13:00:00" and start_time <= "2016-12-19 23:50:00"'
        datosAnalisis = df.query(query)

        # df = df[(df['start_time']>='"'+datetime.strftime(tiempoAnalizarIni, '%Y-%m-%d %H:%M:%S.%f')+'"') & (df['start_time']<='"'+datetime.strftime(tiempoAnalizarFin, '%Y-%m-%d %H:%M:%S.%f')+'"')]
        peak_current = 0 #Corriente pico

        HoraFinalCelula = None
        HoraInicialCelula = None
        EvoPuntoInicial = []
        EvoPuntoFinal = []
        if not datosAnalisis.empty:
            printPosibleWeather = False
            for i, row in enumerate(datosAnalisis.itertuples(),1):
                peak_current += abs(row.peak_current)

                # print(row.latitude,row.longitude)

                # print(row.start_time, abs(row.peak_current))
                if(peak_current >= 1000000):
                    printPosibleWeather = True
                    # Si supera los 1.000.000 de pico de corriente
                    # Generar poligono de los ultimos 15 minutos
                    tiempoTormentaIni = tiempoAnalizarIni - timedelta(minutes=180)
                    rs = database_connection.query("SELECT start_time,end_time,type,latitude,longitude,peak_current,ic_height,number_of_sensors,ic_multiplicity,cg_multiplicity,geom FROM lightning_data WHERE type=1 AND ST_DistanceSphere(geom, ST_MakePoint(" + coordenadaAnalizar + ")) <= " + "80000" + "  AND start_time >= to_timestamp('" + str(diaAnalizarIni) + "', 'YYYY-MM-DD HH24:MI:SS.MS') AND start_time <= to_timestamp('" + str(diaAnalizarFin) + "', 'YYYY-MM-DD HH24:MI:SS.MS')")
                    dff = pd.DataFrame(data=rs, columns=['start_time', 'end_time', 'type', 'latitude', 'longitude',
                                                          'peak_current', 'ic_height', 'number_of_sensors',
                                                          'ic_multiplicity', 'cg_multiplicity', 'geom'])

                    if HoraFinalCelula is None:
                        HoraFinalCelula = row.start_time

                    ArrayCentroides = []
                    while tiempoTormentaIni <= tiempoAnalizarIni:
                        tiempoTormentaFin = tiempoTormentaIni + timedelta(minutes=10)
                        query = 'start_time >="' + datetime.strftime(tiempoTormentaIni,'%Y-%m-%d %H:%M:%S') + '" and start_time<="' + datetime.strftime(tiempoTormentaFin, '%Y-%m-%d %H:%M:%S') + '"'
                        tormentaAnalisis = dff.query(query)
                        if not datosAnalisis.empty:
                            fileName = False
                            points = []
                            qty = 0
                            for k, r in enumerate(tormentaAnalisis.itertuples(), 1):
                                qty+=1
                                plot.drawIntoMap(r.longitude, r.latitude, r.type)
                                points.append([r.longitude, r.latitude])
                                if fileName == False:
                                    # Convertir hora UTC a hora local UTC -3
                                    horaEvento = r.start_time
                                    # horaEvento = row.start_time - timedelta(hours=3)
                                    fileName = str(horaEvento).replace(":", "").replace(".", "")
                                    fileName = "celula_inicial_"+fileName
                                    if HoraInicialCelula is None:
                                        HoraInicialCelula = horaEvento

                            if fileName:
                                # points = np.array(points)
                                points = np.array(points)

                                if qty>=3:
                                    hull = ConvexHull(points, qhull_options="QJ")
                                    plot.draw(points, hull)
                                    # Get centroid
                                    cx = np.mean(hull.points[hull.vertices, 0])
                                    cy = np.mean(hull.points[hull.vertices, 1])

                                    if not EvoPuntoInicial:
                                        EvoPuntoInicial = [cx,cy]

                                    EvoPuntoFinal = [cx,cy]

                                    ArrayCentroides.append([cx,cy])

                                    # Una vez tengamos el centroid debemos ir tomando diferentes poligonos en un lapso de 15-20 minutos atras del 1000000 miliampereos
                                    # obtener lo sigiente:
                                    # velocidad segun distancia del primer poligono al ultimo en los 15-20 minutos
                                    # distancia del futuro punto en 20 minutos
                                    # angulo de curvatura entre ultimo, anteoultimo y penultimo poligono

                                    # print("Centroid X:"+str(cx)+" Centroid Y:"+str(cy))
                                    plot.drawIntoMap(cx, cy, 2)

                                plot.saveToFile(fileName)
                                plot = plt.Plot()

                        tiempoTormentaIni = tiempoTormentaFin

                    # print("########")
                    # print("Posible evento severo. Amperaje de:", peak_current)
                    plot.drawIntoMap(row.longitude, row.latitude, row.type)
                    # Convertir hora UTC a hora local UTC -3
                    # horaEvento = row.start_time - timedelta(hours=3)
                    # print(horaEvento)
                    fileName = str(row.start_time).replace(":","").replace(".","")
                    plot.saveToFile(fileName)
                    plot = plt.Plot()
                    # print("Inicio:"+str(EvoPuntoInicial)+" final:"+str(EvoPuntoFinal))
            if(printPosibleWeather):
                fileName = False
                qty = 0
                points = []
                for i,row in enumerate(datosAnalisis.itertuples(),1):
                    plot.drawIntoMap(row.longitude,row.latitude,row.type)
                    qty += 1
                    points.append([row.longitude, row.latitude])
                    if fileName==False:
                        # Convertir hora UTC a hora local UTC -3
                        horaEvento = row.start_time
                        horaEvento = row.start_time - timedelta(hours=3)
                        fileName = str(horaEvento).replace(":", "").replace(".", "")

                points = np.array(points)
                hull = ConvexHull(points)
                plot.draw(points, hull)

                # Get centroid
                cx = np.mean(hull.points[hull.vertices, 0])
                cy = np.mean(hull.points[hull.vertices, 1])


                if ArrayCentroides:
                    ArrayCentroides.append([cx, cy])

                # Una vez tengamos el centroid debemos ir tomando diferentes poligonos en un lapso de 15-20 minutos atras del 1000000 miliampereos
                # obtener lo sigiente:
                # velocidad segun distancia del primer poligono al ultimo en los 15-20 minutos
                # distancia del futuro punto en 20 minutos
                # angulo de curvatura entre ultimo, anteoultimo y penultimo poligono

                #print("Centroid X:"+str(cx)+" Centroid Y:"+str(cy))
                plot.drawIntoMap(cx,cy,2)

                plot.saveToFile(fileName)
                # plot = plt.Plot()
                printPosibleWeather = False

            if EvoPuntoFinal and EvoPuntoInicial:
                distancia = MedirDistancia(EvoPuntoInicial[0],EvoPuntoInicial[1], EvoPuntoFinal[0],EvoPuntoFinal[1])
                if HoraInicialCelula and HoraFinalCelula:
                    tiempoDesplazamiento = HoraFinalCelula - HoraInicialCelula
                    tiempoDesplazamiento = tiempoDesplazamiento / timedelta(hours=1)
                    velocidad = distancia/tiempoDesplazamiento


                    X = [point[0] for point in ArrayCentroides]
                    X = np.array(X)
                    Y = [point[1] for point in ArrayCentroides]
                    Y = np.array(Y)

                    # Dibujamos los datos para poder visualizarlos y ver si sería lógico
                    # considerar el ajuste usando un modelo lineal
                    # plot(X, Y, 'o')

                    # Para dibujar la recta
                    # plot = plt.Plot()
                    plot.drawIntoMap(X,Y,3)



                    # Calculamos los coeficientes del ajuste (a X + b)
                    a, b = np.polyfit(X, Y, 1)
                    # Calculamos el coeficiente de correlación
                    r = np.corrcoef(X, Y)
                    # Dibujamos los datos para poder visualizarlos y ver si sería lógico
                    # considerar el ajuste usando un modelo lineal
                    # Coordenadas X e Y sobre la recta
                    # (np.max(X), a * np.max(X) + b, '+')

                    nueva_distancia = velocidad * 0.16  # velocidad de desplazamiento * tiempo esperado de llegada en horas
                    nuevo_x, nuevo_y = CalcularSigtePunto(np.min(X), a * np.min(X) + b, np.max(X),a* np.max(X) + b, nueva_distancia)
                    # plot = plt.Plot()
                    plot.drawIntoMap(nuevo_x, nuevo_y, 4)
                    fileName = "punto_futuro"
                    plot.saveToFile(fileName)

                    print("Se desplazó " + str(distancia) + "km en " + str(
                        tiempoDesplazamiento) + " horas. A una velocidad de " + str(
                        velocidad) + " km/h" + " nueva Lat:" + str(nuevo_x) + " Lon:" + str(nuevo_y))

                    plot.saveToFile(fileName)
                    plot = plt.Plot()


        tiempoAnalizarIni = tiempoAnalizarFin
        tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)
    # plot.printMap()

    tiempo_final = time.time()
    tiempo_transcurrido = tiempo_final - inicio_de_tiempo
    print("Tiempo transcurrido de análisis: "+str(tiempo_transcurrido) + " segundos")
    exit(0)

    """"
    1. Recorrer por tipo de descarga
    2. Recorrer mientras tiempo incio sea menor a tiempo final
    3. Sumar tiempo en lapso de 10 minutos
    4. recoger descargas dentro de coordenadas dadas, tipo de rayo y tiempo inicio y fin
    5. Sumar valor absoluto de peak_current
    6. detectar peak_current mayor a 1.000.000 de Amperios        
    """
