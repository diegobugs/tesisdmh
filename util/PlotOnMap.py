import geojson
import numpy as np
from sklearn import linear_model

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
        a, b = np.polyfit(x, y, 1)
        y = (a * x + b)

        self.geoRayos.append(geojson.Feature(geometry=geojson.LineString([(np.min(x),np.min(y)),(np.max(x),np.max(y))])))

    def addFeature(self, x, y, prop={}):
        self.geoRayos.append(geojson.Feature(geometry=geojson.Point((x, y)), properties=prop))

    def getFeatureCollection(self,title=''):
        self.geoCollection = geojson.FeatureCollection(self.geoRayos)
        self.geoCollection.update({'title':title})
        return self.geoCollection

    def dumpGeoJson(self, FeatureCollection, source='map.geojson'):
        dump = geojson.dumps(FeatureCollection)
        return dump
        # with open(source, 'w') as file:
        #     file.write(dump)