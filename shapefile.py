# First example using shapefile and shapely:
import pandas as pd
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

dato = "dataset/1.csv"


polygon = Polygon([(-27.930452,-57.444440),(-25.596055,-56.774274),(-25.962093,-54.357282),(-29.204053,-55.324079),(-27.930452,-57.444440)])

#print(polygon.contains(point))

rowsAnalized=0
raios= 0
timesThousands = 1

for row in pd.read_csv(dato,sep=',', chunksize=1):
    latitude = row.latitude.item()
    longitude = row.longitude.item()
    rowsAnalized+=1
    point = Point (latitude, longitude)
    if(polygon.contains(point)):
       raios=+1
       #print(point)
    if(rowsAnalized==(10000*timesThousands)):
        print(rowsAnalized)
        timesThousands+=1

print(rowsAnalized)
print("Rayos adentro:",raios,sep=" ")

