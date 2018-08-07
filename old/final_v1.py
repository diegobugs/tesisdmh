
import pandas as pd
from util import DatabaseConnection as db
from util import PlotData as plt
from datetime import datetime
from datetime import timedelta
import time
import csv

if __name__ == '__main__':

    inicio_de_tiempo = time.time()

    database_connection = db.DatabaseConnection('','rayos','cta','')

    diaAnalizarIni = datetime.strptime('2016-11-27 13:00:00', '%Y-%m-%d %H:%M:%S')
    diaAnalizarFin = datetime.strptime('2016-11-27 17:00:00', '%Y-%m-%d %H:%M:%S')
    coordenadaAnalizar = '-57.606765,-25.284659'  # Asuncion2
    tiempoIntervalo = 10  # minutos
    diametroAnalizar = '45000'  # en metros

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
    analisis_data = []
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
        query = 'fecha_observacion >="' + datetime.strftime(tiempoAnalizarIni + timedelta(minutes=0),'%Y-%m-%d %H:%M:%S') + '" and fecha_observacion < "' + datetime.strftime(tiempoAnalizarIni + timedelta(minutes=10), '%Y-%m-%d %H:%M:%S') + '"'
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

        analisis_data.append([tiempoAnalizarIni, peak_current, precipitacion])


        # Mostrar en pantalla Hora analizada, intensidad y densidad de descargas electricas
        if printPosibleWeather:
            print("Hora " + str(tiempoAnalizarIni) + " Intensidad:" + str(peak_current) + " Densidad:" + str(qty)+" Precipitacion:"+str(precipitacion)+" Estaciones:"+str(qtyE))
        # endif

        tiempoAnalizarIni = tiempoAnalizarFin
        tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)

    fileName = "Analisis_" + str(diaAnalizarIni).replace(":", "").replace(".", "") + "_" + str(
        diaAnalizarFin).replace(":",
                                "").replace(
        ".", "")

    pd.DataFrame(data=analisis_data,
                 columns=['Fecha_Hora', 'Intensidad', 'Precipitacion']).to_csv("analisis/" + fileName + ".csv", sep=";", mode='a',
                                                index=False,
                                                header=False, quoting=csv.QUOTE_NONNUMERIC)
    #endwhile recorrido de tiempo de analisis

    tiempo_final = time.time()
    tiempo_transcurrido = tiempo_final - inicio_de_tiempo
    print("Tiempo transcurrido de análisis: " + str(tiempo_transcurrido) + " segundos")
    exit(0)
