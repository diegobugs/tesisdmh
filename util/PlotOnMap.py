import geojson
import time
import numpy as np
from numpy.linalg import lstsq

# rayo = geojson.Feature(geometry=geojson.Point((-55.628954, -27.009561)))
# otrorayo = geojson.Feature(geometry=geojson.Point((-55.530334, -27.000346)))
# dump = geojson.dumps(geojson.FeatureCollection([rayo, otrorayo]), sort_keys='True')
# with open('map.geojson', 'w') as file:
#     file.write(dump)

class PlotOnGeoJSON:

    def __init__(self):
        # Conjunto de rayos
        self.geoRayos = []

    def draw(self, points, hull):
        polyPoints = []
        for simplex in hull.vertices:
            x, y = points[simplex, 0], points[simplex, 1]
            polyPoints.append([x, y])

        self.geoRayos.append(geojson.Feature(geometry=geojson.Polygon([polyPoints])))

    def makePath(self, x, y):
        self.geoRayos.append(geojson.Feature(geometry=geojson.LineString([(np.min(x),np.min(y)),(np.max(x),np.max(y))])))

    def addFeature(self, x, y):
        self.geoRayos.append(geojson.Feature(geometry=geojson.Point((x, y))))

    def getFeatureCollection(self):
        self.geoCollection = geojson.FeatureCollection(self.geoRayos)
        return self.geoCollection

    def dumpGeoJson(self, FeatureCollection, source='map.geojson'):
        dump = geojson.dumps(FeatureCollection)
        return dump
        # with open(source, 'w') as file:
        #     file.write(dump)