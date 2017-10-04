import enipy as lx	#so we can read the data
import csv
import pandas as pd
from matplotlib import path

# POLIGONO DE ASUNCION CENTRO
#POLIGONO = path.Path([(-25.273395,-57.649131),(-25.291854,-57.670566),(-25.379863,-57.623205),(-25.282071,-57.540120),(-25.254011,-57.584827),(-25.273395,-57.649131)])

#POLIGONO DE ENCARNACION
POLIGONO = path.Path([(-27.275677,-56.648758),(-26.932586,-56.100027),(-27.287288,-55.678680),(-27.548231,-55.959578),(-27.275677,-56.648758)])


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
raios=0
rowsAnalized = 0
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
    if(rowsAnalized>10000):
        print(rowsAnalized)
        rowsAnalized=0


print("Rayos adentro:",raios,sep=" ")
