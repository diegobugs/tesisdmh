import osgeo.ogr
import glob

path = "/home/gabriel/PycharmProjects/tesisdmh/dataset/poligono/"
out = path + 'output.txt'

file = open(out,'w')
for filename in glob.glob(path + "*.shp"):
    ds = osgeo.ogr.Open(filename)
    layer1 = ds.GetLayer(0)
    print(layer1.GetExtent())
    for feat in layer1:
        geom = feat.GetGeometryRef()
        ring = geom.GetGeometryRef(0)
        points = ring.GetPointCount()
        #Not sure what to do here
        for p in range (points):
            lon, lat, z = ring.GetPoint (p)
            file.write("(" + str(lat) + ",")
            file.write (str(lon) + "),")
file.close()
