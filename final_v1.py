
import pandas as pd
from util import DatabaseConnection as db
from util import PlotData as plt
from datetime import datetime
from datetime import timedelta
import time


if __name__ == '__main__':

    inicio_de_tiempo = time.time()
    database_connection = db.DatabaseConnection()

    diaAnalizarIni = datetime.strptime('2016-11-27 00:40:00', '%Y-%m-%d %H:%M:%S')
    diaAnalizarFin = datetime.strptime('2016-11-27 22:30:00', '%Y-%m-%d %H:%M:%S')
    coordenadaAnalizar = '-57.606765,-25.284659'  # Asuncion2
    tiempoIntervalo = 10  # minutos
    diametroAnalizar = '40000'  # en metros

    tiempoAnalizarIni = diaAnalizarIni
    tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)

    rows = database_connection.query(
        "SELECT start_time,end_time,type,latitude,longitude,peak_current,ic_height,number_of_sensors,ic_multiplicity,cg_multiplicity,geom FROM lightning_data WHERE type=1 AND ST_DistanceSphere(geom, ST_MakePoint(" + coordenadaAnalizar + ")) <= " + diametroAnalizar + "  AND start_time >= to_timestamp('" + str(
            diaAnalizarIni) + "', 'YYYY-MM-DD HH24:MI:SS.MS') AND start_time <= to_timestamp('" + str(
            diaAnalizarFin) + "', 'YYYY-MM-DD HH24:MI:SS.MS')")

    df = pd.DataFrame(data=rows,columns=['start_time', 'end_time', 'type', 'latitude', 'longitude', 'peak_current', 'ic_height','number_of_sensors', 'ic_multiplicity', 'cg_multiplicity', 'geom'])

    while tiempoAnalizarIni <= diaAnalizarFin:
        query = 'start_time >="' + datetime.strftime(tiempoAnalizarIni,'%Y-%m-%d %H:%M:%S') + '" and start_time<="' + datetime.strftime(tiempoAnalizarFin, '%Y-%m-%d %H:%M:%S') + '"'
        datosAnalisis = df.query(query)

        peak_current = 0  # Corriente pico
        HoraFinalCelula = None
        HoraInicialCelula = None
        EvoPuntoInicial = []
        EvoPuntoFinal = []
        if not datosAnalisis.empty:
            printPosibleWeather = False
            for i, row in enumerate(datosAnalisis.itertuples(),1):
                peak_current += abs(row.peak_current)

                if (peak_current >= 1000000):
                    printPosibleWeather = True

                    # Si supera los 1.000.000 de pico de corriente
                    # Generar poligono de los ultimos 15 minutos
                    tiempoTormentaIni = tiempoAnalizarIni - timedelta(minutes=180)
                    # rs = database_connection.query(
                    #     "SELECT start_time,end_time,type,latitude,longitude,peak_current,ic_height,number_of_sensors,ic_multiplicity,cg_multiplicity,geom FROM lightning_data WHERE type=1 AND ST_DistanceSphere(geom, ST_MakePoint(" + coordenadaAnalizar + ")) <= " + "80000" + "  AND start_time >= to_timestamp('" + str(
                    #         diaAnalizarIni) + "', 'YYYY-MM-DD HH24:MI:SS.MS') AND start_time <= to_timestamp('" + str(
                    #         diaAnalizarFin) + "', 'YYYY-MM-DD HH24:MI:SS.MS')")
                    # dff = pd.DataFrame(data=rs, columns=['start_time', 'end_time', 'type', 'latitude', 'longitude',
                    #                                      'peak_current', 'ic_height', 'number_of_sensors',
                    #                                      'ic_multiplicity', 'cg_multiplicity', 'geom'])

                    if HoraFinalCelula is None:
                        HoraFinalCelula = row.start_time

                    ArrayCentroides = []

        tiempoAnalizarIni = tiempoAnalizarFin
        tiempoAnalizarFin = tiempoAnalizarIni + timedelta(minutes=tiempoIntervalo)

    tiempo_final = time.time()
    tiempo_transcurrido = tiempo_final - inicio_de_tiempo
    print("Tiempo transcurrido de análisis: " + str(tiempo_transcurrido) + " segundos")
    exit(0)