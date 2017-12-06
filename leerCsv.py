import csv
# import pandas as pd
import  time


inFile = 'dataset/1.csv'

rowsAnalized = 0
inicio_de_tiempo = time.time()

# for row in pd.read_csv(inFile,sep=',', chunksize=1):
#     latitude = row.latitude.item()
#     longitude = row.longitude.item()
#     rowsAnalized+=1

a = open(inFile, 'rt')
reader = csv.reader(a)
for row in reader:
    # print(row)
    rowsAnalized += 1

a.close()

tiempo_final = time.time()
tiempo_transcurrido = tiempo_final - inicio_de_tiempo
print("Registros analizados: "+str(rowsAnalized)+" en "+str(tiempo_transcurrido)+" segundos")