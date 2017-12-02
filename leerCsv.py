import csv
import pandas as pd
import  time


inFile = 'dataset/1.csv'

_columns = ["type",
               "timestamp",
               "latitude",
               "longitude",
               "peakcurrent",
               "icheight",
               "numbersensors",
               "icmultiplicity",
               "cgmultiplicity",
               "starttime",
               "endtime",
               "duration",
               "ullatitude",
               "ullongitude",
               "lrlatitude",
               "lrlongitude"]

rowsAnalized = 0
inicio_de_tiempo = time.time()

for row in pd.read_csv(inFile,sep=',', chunksize=1):
    latitude = row.latitude.item()
    longitude = row.longitude.item()
    rowsAnalized+=1

tiempo_final = time.time()
tiempo_transcurrido = tiempo_final - inicio_de_tiempo
print("Registros analizados: "+str(rowsAnalized)+" en "+str(tiempo_transcurrido)+" segundos")