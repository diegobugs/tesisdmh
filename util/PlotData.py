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


        lllon = -58.5200500488
        urlon = -56.6290283203
        lllat = -26.2010377682
        urlat = -24.4271453401

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
            self.m.plot(x, y, 'r--', lw=0.2)

        # self.m.plot(points[hull.vertices, 0], points[hull.vertices, 1], 'r--', lw=2)
        # self.m.plot(points[hull.vertices[0], 0], points[hull.vertices[0], 1], 'ro')


    def drawIntoMap(self,x,y,type):
        # -57.623154, -25.280073
        x, y = self.m(x,y)

        if type==1 or type==0:
            marker = '+' #rayos
            markersize = 0.2
            color = "red"
        else:
            marker = 'o' #centro
            markersize = 0.4
            color = "green"

        self.m.plot(x, y, marker, markersize=markersize, color=color)

    def saveToFile(self,fileName="img_"+time.strftime("%Y%m%d-%H%M%S%M"),extension="png"):
        plt.title(fileName)
        plt.savefig("png/"+fileName+"."+extension,dpi=600)
        plt.close()


    def printMap(self):
        # Get rid of some of the extraneous whitespace matplotlib loves to use.
        # plt.tight_layout(pad=0, w_pad=0, h_pad=0)
        plt.show()