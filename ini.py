import enipy as lx	#so we can read the data
import csv
import pandas as pd
from matplotlib import path

# POLIGONO DE ASUNCION CENTRO
#POLIGONO = path.Path([(-25.273395,-57.649131),(-25.291854,-57.670566),(-25.379863,-57.623205),(-25.282071,-57.540120),(-25.254011,-57.584827),(-25.273395,-57.649131)])

#POLIGONO DE ENCARNACION
POLIGONO = path.Path([(-27.930452,-57.444440),(-25.596055,-56.774274),(-25.962093,-54.357282),(-29.204053,-55.324079),(-27.930452,-57.444440)])


def inside_polygon(x, y, POLIGONO):
    IsInside = POLIGONO.contains_points([(x,y)])
    return IsInside

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
rowsAnalized=0
raios= 0
timesThousands = 1
for row in pd.read_csv(inFile,sep=',', chunksize=1):
    latitude = row.latitude.item()
    longitude = row.longitude.item()
    rowsAnalized+=1
    if(inside_polygon(latitude,longitude,POLIGONO)):
       raios=+1
    if(raios>1):
        print(latitude)
        print(longitude)
        break
    if(rowsAnalized==(10000*timesThousands)):
        print(rowsAnalized)
        timesThousands+=1

print(rowsAnalized)
print("Rayos adentro:",raios,sep=" ")
