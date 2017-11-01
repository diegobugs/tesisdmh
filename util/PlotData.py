from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import time

class Plot:

    def __init__(self):
        # Set the lower left and upper right limits of the bounding box:
        lllon = -62.6509765625
        urlon = -54.241796875
        lllat = -27.5538085938
        urlat = -19.2862304688

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

    def drawIntoMap(self,x,y,type):
        # -57.623154, -25.280073
        x, y = self.m(x,y)
        self.m.plot(x, y, 'bo', markersize=0.2)

    def saveToFile(self,fileName="img_"+time.strftime("%Y%m%d-%H%M%S%M"),extension="png"):
        plt.savefig("png/"+fileName+"."+extension,dpi=600)
        plt.close()


    def printMap(self):
        plt.title('Paraguay')
        # Get rid of some of the extraneous whitespace matplotlib loves to use.
        # plt.tight_layout(pad=0, w_pad=0, h_pad=0)
        plt.show()