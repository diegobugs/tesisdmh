from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import time
import numpy as np

class Plot:

    def __init__(self):
        # Set the lower left and upper right limits of the bounding box:

        # All PARAGUAY box
        # lllon = -62.6509765625
        # urlon = -54.241796875
        # lllat = -27.5538085938
        # urlat = -19.2862304688


        # # Central Box
        # lllon = -58.5200500488
        # urlon = -56.6290283203
        # lllat = -26.2010377682
        # urlat = -24.4271453401

        # # Encarnacion Box
        lllon = -56.606127
        urlon = -55.052012
        lllat = -27.707004
        urlat = -26.861432

        # [[[-62.75390625, -27.5082714139], [-54.1186523437, -27.5082714139], [-54.1186523437, -19.2074285268],
        #   [-62.75390625, -19.2074285268], [-62.75390625, -27.5082714139]]]
        #
        # [[[-58.5200500488, -26.2010377682], [-56.6290283203, -26.2010377682], [-56.6290283203, -24.4271453401],
        #   [-58.5200500488, -24.4271453401], [-58.5200500488, -26.2010377682]]]

        # and calculate a centerpoint, needed for the projection:
        centerlon = float(lllon + urlon) / 2.0
        centerlat = float(lllat + urlat) / 2.0

        self.m = Basemap(resolution='i',  # crude, low, intermediate, high, full
                    llcrnrlon=lllon, urcrnrlon=urlon,
                    lon_0=centerlon,
                    llcrnrlat=lllat, urcrnrlat=urlat,
                    lat_0=centerlat,
                    projection='tmerc')

        # Read state boundaries.
        shp_info =self.m.readshapefile('dataset/shp/PRY_adm1', 'states',
                                   drawbounds=True, color='black')

        # Read county boundaries
        # shp_info = m.readshapefile('dataset/shp/PRY_adm2',
        #                            'counties',
        #                            drawbounds=True)
    def draw(self,points,hull):
        for simplex in hull.simplices:
            x, y = self.m(points[simplex, 0], points[simplex, 1])
            self.m.plot(x, y, 'r--', lw=0.1)

        # self.m.plot(points[hull.vertices, 0], points[hull.vertices, 1], 'r--', lw=2)
        # self.m.plot(points[hull.vertices[0], 0], points[hull.vertices[0], 1], 'ro')


    def drawIntoMap(self,x,y,type):
        # -57.623154, -25.280073
        x, y = self.m(x,y)

        if type==1 or type==0:
            marker = '+' #rayos
            markersize = 0.2
            color = "red"
        if type==2:
            marker = 'o' #centro
            markersize = 0.2
            color = "green"
        if type==3:
            marker = '.'  # centro
            markersize = 0.2
            color = "green"
            # Calculamos los coeficientes del ajuste (a X + b)
            a, b = np.polyfit(x, y, 1)
            # Calculamos el coeficiente de correlación
            r = np.corrcoef(x, y)
            # Dibujamos los datos para poder visualizarlos y ver si sería lógico
            # considerar el ajuste usando un modelo lineal
            self.m.plot(x, y, marker, markersize=markersize, color=color)
            self.m.plot(np.min(x) - 1, np.max(x) + 1)
            self.m.plot(np.min(y) - 1, np.max(y) + 1)
            self.m.plot(x, a * x + b)
            # plt.text(4, 10, 'r = {0:2.3f}'.format(r[0, 1]))
            # plt.text(4, 9, 'Y = {0:2.3f} X + {1:2.3f}'.format(a, b))

        self.m.plot(x, y, marker, markersize=markersize, color=color)

    def saveToFile(self,fileName="img_"+time.strftime("%Y%m%d-%H%M%S%M"),extension="png"):
        plt.title(fileName)
        plt.savefig("png/"+fileName+"."+extension,dpi=300)
        plt.close()

    def saveToGeoJSON(self):
        plt.close()

    def printMap(self):
        # Get rid of some of the extraneous whitespace matplotlib loves to use.
        # plt.tight_layout(pad=0, w_pad=0, h_pad=0)
        plt.show()